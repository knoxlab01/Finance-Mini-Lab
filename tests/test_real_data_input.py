"""Synthetic UNIT TEST inputs only, in temporary directories, never private_data."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from research.real_data_loader import load_local_dataset, DEFAULT_TICKERS, ROOT
from research.real_data_check import main, private_git_status
from src.evolance.v1_1.spec import SPEC_SHA256


class LocalInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def make(self, n=1400, field="Adj Close", date_column="Date", wide=False, metadata=True):
        dates = pd.bdate_range("2010-01-01", periods=n)
        values = 100 + np.arange(n) / 100
        if wide:
            frame = pd.DataFrame({date_column: dates})
            for symbol in DEFAULT_TICKERS:
                frame[symbol] = values
            frame.to_csv(self.directory / "wide.csv", index=False)
        else:
            for symbol in DEFAULT_TICKERS:
                pd.DataFrame({date_column: dates, field: values}).to_csv(self.directory / (symbol + ".csv"), index=False)
        manifest = dict(dataset_name="SYNTHETIC_UNIT_TEST_ONLY", source="deterministic synthetic test fixture; not actual market history",
                        download_date="2026-10-09", usage_context="unit test only", asset_class="equity",
                        price_type="adjusted_close" if field != "Close" else "close", tickers=list(DEFAULT_TICKERS), benchmark="SPY", notes="Synthetic")
        if metadata:
            self.write_manifest(manifest)
        return dates, values

    def write_manifest(self, value):
        (self.directory / "manifest.json").write_text(json.dumps(value), encoding="utf-8")

    def change(self, ticker, fn):
        path = self.directory / (ticker + ".csv")
        frame = pd.read_csv(path)
        fn(frame).to_csv(path, index=False)

    def load(self, **kwargs):
        return load_local_dataset(self.directory, **kwargs)

    def test_per_ticker_ready(self):
        self.make()
        result = self.load()
        self.assertEqual(result.report["status"], "READY")
        self.assertEqual(result.prices.shape, (1400, 4))
        self.assertTrue(result.report["fully_research_ready"])
        self.assertTrue(result.report["evolance_v1_1_compatible"])
        self.assertGreater(result.report["window_coverage"]["12M_complete_windows"], 0)
        self.assertEqual(result.report["spec_sha256"], SPEC_SHA256)

    def kaggle_fixture(self):
        self.make(field="Close")
        manifest=json.loads((self.directory/'manifest.json').read_text())
        manifest.update(source="Kaggle Huge Stock Market Dataset", author="Boris Marjanovic",
                        price_type="source_adjusted_close", source_adjusted_close_opt_in=True)
        self.write_manifest(manifest)
        for ticker in DEFAULT_TICKERS:
            (self.directory/(ticker+'.csv')).rename(self.directory/(ticker.lower()+'.us.txt'))
        return manifest

    def test_kaggle_four_files_source_adjusted_close(self):
        self.kaggle_fixture()
        before={p.name:p.read_bytes() for p in self.directory.iterdir()}
        result=self.load()
        self.assertEqual(result.report['status'],'READY')
        self.assertEqual(result.prices.shape,(1400,4))
        for ticker in DEFAULT_TICKERS:
            info=result.report['per_ticker'][ticker]
            self.assertEqual(info['chosen_price_field'],'Close')
            self.assertEqual(info['price_type'],'source_adjusted_close')
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.directory.iterdir()})
        for ticker in DEFAULT_TICKERS:
            (self.directory/(ticker.lower()+'.us.txt')).rename(self.directory/(ticker.lower()+'.us'))
        self.assertEqual(self.load().report['status'],'READY')

    def test_source_adjusted_requires_provenance_and_boolean_opt_in(self):
        manifest=self.kaggle_fixture()
        for field,value in [('source','unrelated source'),('author','unknown'),
                            ('source_adjusted_close_opt_in',False),('source_adjusted_close_opt_in','true')]:
            with self.subTest(field=field,value=value):
                self.write_manifest(dict(manifest,**{field:value}))
                result=self.load()
                self.assertEqual(result.report['status'],'NOT_READY')
                self.assertEqual(result.report['per_ticker']['AAPL']['price_type'],'close')

    def test_kaggle_filename_alone_does_not_upgrade_close(self):
        self.kaggle_fixture()
        (self.directory/'manifest.json').unlink()
        result=self.load()
        self.assertEqual(result.report['status'],'READY_WITH_WARNINGS')
        self.assertEqual(result.report['per_ticker']['AAPL']['price_type'],'close')
        self.assertIn('ordinary_close',[w['code'] for w in result.report['warnings']])

    def test_wide_ready_with_declared_convention(self):
        self.make(wide=True)
        result = self.load()
        self.assertEqual(result.report["status"], "READY")
        self.assertEqual(list(result.prices.columns), list(DEFAULT_TICKERS))

    def test_date_and_adjusted_aliases_case_insensitive(self):
        self.make()
        for i, alias in enumerate(["Adj Close", "Adjusted Close", "adjusted_close", "adjusted close", "adj_close", "adjusted"]):
            with self.subTest(alias=alias):
                dates = ["dAtE", "Datetime", "TIMESTAMP"]
                frame = pd.read_csv(self.directory / "AAPL.csv")
                frame.columns = [dates[i % 3], alias]
                frame.to_csv(self.directory / "AAPL.csv", index=False)
                result = self.load()
                self.assertEqual(result.report["status"], "READY")
                self.assertEqual(result.report["per_ticker"]["AAPL"]["chosen_price_field"], alias)

    def test_adjusted_priority_over_close(self):
        _, prices = self.make()
        self.change("AAPL", lambda f: f.assign(Close=f["Adj Close"] + 100))
        result = self.load()
        np.testing.assert_allclose(result.prices.AAPL.to_numpy(), prices, rtol=0, atol=1e-12)
        self.assertEqual(result.report["per_ticker"]["AAPL"]["price_type"], "adjusted_close")

    def test_close_warns_and_cannot_be_upgraded_by_manifest(self):
        self.make(field="Close")
        manifest=json.loads((self.directory/"manifest.json").read_text())
        manifest["price_type"]="adjusted_close"
        self.write_manifest(manifest)
        result=self.load()
        self.assertEqual(result.report["status"],"READY_WITH_WARNINGS")
        self.assertFalse(result.report["fully_research_ready"])
        self.assertEqual(result.report["per_ticker"]["AAPL"]["price_type"],"close")
        self.assertIn("ordinary_close",[w["code"] for w in result.report["warnings"]])

    def test_exact_duplicates_and_descending_dates(self):
        self.make()
        self.change("AAPL",lambda f:pd.concat([f,f.iloc[[100]]],ignore_index=True).iloc[::-1])
        result=self.load()
        self.assertEqual(result.report["status"],"READY")
        self.assertEqual(result.report["per_ticker"]["AAPL"]["duplicate_rows_removed"],1)
        self.assertTrue(result.prices.index.is_monotonic_increasing)

    def test_conflicting_duplicates_rejected(self):
        self.make()
        self.change("AAPL",lambda f:pd.concat([f,f.iloc[[100]].assign(**{"Adj Close":999})],ignore_index=True))
        result=self.load()
        self.assertEqual(result.report["status"],"NOT_READY")
        self.assertIsNone(result.prices)
        self.assertIn("conflicting_duplicates",[e["code"] for e in result.report["errors"]])

    def test_missing_and_present_duplicate_conflict(self):
        self.make()
        self.change("AAPL",lambda f:pd.concat([f,f.iloc[[100]].assign(**{"Adj Close":np.nan})],ignore_index=True))
        self.assertIn("conflicting_duplicates",[e["code"] for e in self.load().report["errors"]])

    def test_zero_negative_infinite_and_malformed_rejected(self):
        for value in [0,-1,np.inf,"not-a-price"]:
            with self.subTest(value=value):
                self.make()
                def mutate(frame):
                    frame["Adj Close"]=frame["Adj Close"].astype(object)
                    frame.loc[100,"Adj Close"]=value
                    return frame
                self.change("AAPL",mutate)
                result=self.load()
                self.assertEqual(result.report["status"],"NOT_READY")
                self.assertIn("invalid_prices",[e["code"] for e in result.report["errors"]])

    def test_nan_alignment_no_forward_or_backfill(self):
        dates,_=self.make()
        def mutate(frame):
            frame.loc[100,"Adj Close"]=np.nan
            frame["Close"]=999.
            return frame
        self.change("AAPL",mutate)
        result=self.load()
        self.assertEqual(result.report["status"],"READY_WITH_WARNINGS")
        self.assertNotIn(dates[100],result.prices.index)
        self.assertEqual(len(result.prices),1399)
        self.assertEqual(result.report["per_ticker"]["AAPL"]["missing_price_count"],1)
        self.assertEqual(result.report["per_ticker"]["SPY"]["dropped_valid_dates_by_alignment"],1)

    def test_different_start_end_dates_intersect(self):
        dates,_=self.make()
        self.change("AAPL",lambda f:f.iloc[20:-10])
        result=self.load()
        self.assertEqual(result.prices.index[0],dates[20])
        self.assertEqual(result.prices.index[-1],dates[-11])
        self.assertEqual(result.report["per_ticker"]["SPY"]["dropped_valid_dates_by_alignment"],30)

    def test_missing_ticker(self):
        self.make()
        (self.directory/"NVDA.csv").unlink()
        result=self.load()
        self.assertEqual(result.report["status"],"NOT_READY")
        self.assertTrue(any(e.get("ticker")=="NVDA" and e["code"]=="missing_ticker" for e in result.report["errors"]))

    def test_short_history_and_month_end_requirement(self):
        for n in [252,504,505]:
            with self.subTest(n=n):
                self.make(n=n)
                result=self.load()
                self.assertEqual(result.report["status"],"NOT_READY")
                self.assertEqual(result.report["window_coverage"]["12M_complete_windows"],0)

    def test_usable_under_five_years_is_warning_not_rejected(self):
        self.make(n=600)
        result=self.load()
        self.assertEqual(result.report["status"],"READY_WITH_WARNINGS")
        self.assertTrue(result.report["evolance_v1_1_compatible"])
        self.assertIn("limited_history",[w["code"] for w in result.report["warnings"]])

    def test_large_aligned_gap_not_compatible(self):
        self.make()
        self.change("AAPL",lambda f:f.drop(index=range(100,120)))
        result=self.load()
        self.assertEqual(result.report["status"],"NOT_READY")
        self.assertGreater(result.report["largest_aligned_gap_days"],7)

    def test_malformed_date_not_dropped_silently(self):
        self.make()
        def mutate(f):
            f.loc[100,"Date"]="not-a-date"
            return f
        self.change("AAPL",mutate)
        result=self.load()
        self.assertEqual(result.report["status"],"NOT_READY")
        self.assertEqual(result.report["per_ticker"]["AAPL"]["invalid_date_rows"],1)

    def test_timezone_keeps_market_date(self):
        dates,_=self.make()
        self.change("AAPL",lambda f:f.assign(Date=[d.strftime('%Y-%m-%d')+'T23:00:00-05:00' for d in dates]))
        result=self.load()
        self.assertEqual(len(result.prices),1400)
        self.assertEqual(result.prices.index[0],dates[0])
        self.assertIn("timezone_unspecified",[w["code"] for w in result.report["warnings"]])

    def test_declared_date_format(self):
        dates,_=self.make()
        for t in DEFAULT_TICKERS:
            self.change(t,lambda f:f.assign(Date=dates.strftime('%d/%m/%Y')))
        manifest=json.loads((self.directory/"manifest.json").read_text())
        manifest["date_format"]="%d/%m/%Y"
        self.write_manifest(manifest)
        self.assertEqual(self.load().report["status"],"READY")

    def test_declared_timezone_converts_to_market_date(self):
        dates,_=self.make()
        self.change("AAPL",lambda f:f.assign(Date=[(d+pd.Timedelta(days=1)).strftime('%Y-%m-%d')+'T01:00:00Z' for d in dates]))
        manifest=json.loads((self.directory/"manifest.json").read_text())
        manifest["market_timezone"]="America/New_York"
        self.write_manifest(manifest)
        result=self.load()
        self.assertEqual(result.report["status"],"READY")
        self.assertEqual(len(result.prices),1400)
        self.assertEqual(result.prices.index[0],dates[0])

    def test_provenance_missing_and_equity_metadata_preserved(self):
        self.make(metadata=False)
        result=self.load()
        self.assertEqual(result.report["status"],"READY_WITH_WARNINGS")
        self.assertFalse(result.report["evolance_v1_1_compatible"])
        self.make()
        result=self.load()
        self.assertEqual(result.report["provenance"]["asset_class"],"equity")
        self.assertIn("synthetic",result.report["provenance"]["source"])

    def test_crypto_metadata_is_not_equity_validation(self):
        self.make(field="Close")
        manifest=json.loads((self.directory/"manifest.json").read_text())
        manifest.update(asset_class="crypto",tickers=["BTC","ETH","INDEX"],benchmark="INDEX")
        self.write_manifest(manifest)
        for old,new in [("AAPL","BTC"),("MSFT","ETH"),("SPY","INDEX")]:
            (self.directory/(old+'.csv')).rename(self.directory/(new+'.csv'))
        (self.directory/'NVDA.csv').unlink()
        result=self.load(required_tickers=("BTC","ETH","INDEX"),benchmark="INDEX")
        self.assertEqual(result.report["asset_class"],"crypto")
        self.assertFalse(result.report["evolance_v1_1_compatible"])
        self.assertEqual(result.report["status"],"READY_WITH_WARNINGS")
        self.assertNotIn("ordinary_close",[w["code"] for w in result.report["warnings"]])

    def test_wide_unknown_price_type_never_ready(self):
        self.make(wide=True,metadata=False)
        result=self.load()
        self.assertEqual(result.report["status"],"READY_WITH_WARNINGS")
        self.assertEqual(result.report["per_ticker"]["AAPL"]["price_type"],"unknown")

    def test_duplicate_file_source_rejected(self):
        self.make()
        self.make(wide=True)
        self.assertIn("multiple_symbol_sources",[e["code"] for e in self.load().report["errors"]])

    def test_empty_directory_is_not_ready_without_fabrication(self):
        result=self.load()
        self.assertEqual(result.report["status"],"NOT_READY")
        self.assertEqual(list(self.directory.iterdir()),[])

    def test_private_suffix_and_uppercase_extension(self):
        self.make()
        (self.directory/'AAPL.csv').rename(self.directory/'aapl.private.CSV')
        self.assertEqual(self.load().report["status"],"READY")

    def test_sensitive_manifest_fields_rejected_without_echo(self):
        self.make()
        manifest=json.loads((self.directory/'manifest.json').read_text())
        manifest['account_identifier']='synthetic-secret-marker'
        self.write_manifest(manifest)
        report=self.load().report
        self.assertEqual(report['status'],'NOT_READY')
        self.assertNotIn('synthetic-secret-marker',json.dumps(report))

    def test_no_network_model_or_file_mutation(self):
        self.make()
        before={p.name:p.read_bytes() for p in self.directory.iterdir()}
        with patch('src.market_data.download_prices',side_effect=AssertionError('network forbidden')) as network, patch('src.evolance.v1_1.timeline.walk_forward',side_effect=AssertionError('validation forbidden')) as model:
            self.load()
        network.assert_not_called();model.assert_not_called()
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.directory.iterdir()})

    def test_cli_reports_metadata_without_prices(self):
        self.make()
        buffer=io.StringIO()
        with patch('research.real_data_check.private_git_status',return_value=dict(verified=True,issues=[])), contextlib.redirect_stdout(buffer):
            result=main(['--directory',str(self.directory),'--json'])
        self.assertEqual(result,0)
        report=json.loads(buffer.getvalue())
        self.assertFalse(report['final_validation_performed'])
        self.assertNotIn('prices',report)

    def test_cli_blocks_unprotected_inputs(self):
        self.make()
        buffer=io.StringIO()
        with patch('research.real_data_check.private_git_status',return_value=dict(verified=False,issues=['unprotected'])), contextlib.redirect_stdout(buffer):
            result=main(['--directory',str(self.directory),'--json'])
        self.assertEqual(result,2)
        self.assertEqual(json.loads(buffer.getvalue())['status'],'NOT_READY')


class PrivateGitTests(unittest.TestCase):
    def test_ignore_private_inputs_but_keep_public_research_outputs(self):
        for path in ['research/private_data/AAPL.csv','research/private_data/manifest.json','research/private_data/nested/raw.csv','research/local.private.csv']:
            with self.subTest(path=path):
                result=subprocess.run(['git','check-ignore','--no-index','-q','--',path],cwd=ROOT,capture_output=True)
                self.assertEqual(result.returncode,0)
        for path in ['research/REAL_DATA_INPUT.md','research/real_data_manifest.example.json','research/evolance_v1_1_results/fixture_equal_outcomes.csv']:
            self.assertEqual(subprocess.run(['git','check-ignore','--no-index','-q','--',path],cwd=ROOT,capture_output=True).returncode,1)

    def test_private_source_archive_exclusion(self):
        result=subprocess.check_output(['git','check-attr','export-ignore','--','research/private_data/AAPL.csv','research/private_data/manifest.json','research/test.private.csv'],cwd=ROOT,text=True)
        self.assertEqual(result.count('export-ignore: set'),3)

    def test_default_git_protection_verified(self):
        result=private_git_status(ROOT/'research/private_data',ROOT/'research/private_data/manifest.json')
        self.assertTrue(result['verified'],result['issues'])


if __name__=='__main__':
    unittest.main()
