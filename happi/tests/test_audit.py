from abc import ABCMeta
import argparse
from unittest.mock import patch, call
import happi
import json
from happi.audit import Audit, ReportCode
import happi.audit as audit
import pytest
import logging


logger = logging.getLogger(__name__)
audit_class = Audit()
report_code = ReportCode.NO_CODE

ITEMS = json.loads("""{
    "XRT:M3H": {
        "_id": "XRT:M3H",
        "active": true,
        "args": [
            "{{prefix}}"
        ],
        "beamline": "PBT",
        "creation": "Tue Feb 27 16:12:10 2018",
        "device_class": null,
        "kwargs": {
            "name": "{{name}}"
        },
        "last_edit": "Tue Feb 27 16:12:10 2018",
        "macros": null,
        "name": "xrt_m3h",
        "parent": null,
        "prefix": "XRT:M3H",
        "prefix_xy": null,
        "screen": null,
        "stand": null,
        "system": "beam control",
        "type": "something_else",
        "xgantry_prefix": null,
        "z": 927.919
    },
    "XCS:SB2:PIM": {
        "_id": "XCS:SB2:PIM",
        "active": true,
        "args": [
            "{{prefix}}"
        ],
        "beamline": "XCS",
        "creation": "Tue Feb 27 11:15:19 2018",
        "detailed_screen": null,
        "device_class": "pcdsdevices",
        "documentation": null,
        "embedded_screen": null,
        "engineering_screen": null,
        "kwargs": {
            "name": "{{name}}",
            "prefix_det": "{{prefix_det}}"
        },
        "last_edit": "Fri May 17 11:44:12 2019",
        "lightpath": false,
        "macros": null,
        "name": "xcs_sb2_pim",
        "parent": null,
        "prefix": "XCS:SB2:PIM",
        "prefix_det": "XCS:GIGE:04:",
        "screen": null,
        "stand": null,
        "system": null,
        "type": null,
        "z": 1005.72
    },
     "MFX:DG2:IPM": {
        "_id": "MFX:DG2:IPM",
        "active": true,
        "args": [
            "{{prefix}}"
        ],
        "beamline": "MFX",
        "creation": "Wed Mar 27 09:53:48 2019",
        "data": null,
        "detailed_screen": null,
        "device_class": "types.SimpleNamespace",
        "documentation": null,
        "embedded_screen": null,
        "engineering_screen": null,
        "kwargs": {
            "name": "{{name}}"
        },
        "last_edit": "Wed Mar 27 09:53:48 2019",
        "lightpath": false,
        "macros": null,
        "name": "mfx_dg2_ipm",
        "parent": null,
        "prefix": "MFX:DG2:IPM",
        "stand": "DG2",
        "system": "diagnostic",
        "type": "HappiItem",
        "z": -1.0
    },
        "dummy_item": {
        "_id": "dummy_item",
        "active": true,
        "args": [
            "{{prefix}}"
        ],
        "creation": "Thu Sep 10 11:59:23 2020",
        "device_class": "types.SimpleNamespace",
        "documentation": null,
        "kwargs": {
            "name": "{{name}}"
        },
        "last_edit": "Thu Sep 10 11:59:23 2020",
        "name": "dummy_item",
        "prefix": "PREFIX",
        "type": "OphydItem"
    },
        "alias2": {
        "_id": "alias2",
        "active": true,
        "args": [],
        "beamline": "LCLS",
        "creation": "Fri Sep  4 11:31:26 2020",
        "device_class": "pyenvbuilder.types.SimpleNamespace",
        "documentation": null,
        "functional_group": "FUNC",
        "kwargs": {
            "hi": "oh hello"
        },
        "last_edit": "Fri Sep  4 11:31:26 2020",
        "location_group": "LOC",
        "name": "a",
        "prefix": "BASE:PV",
        "type": "OphydItem",
        "z": "400"
    }
    }
    """)


@pytest.fixture(scope='class')
def happi_config(tmp_path_factory, json_db):
    tmp_dir = tmp_path_factory.mktemp('happi.cfg')
    happi_cfg_path = tmp_dir / 'happi.cfg'
    happi_cfg_path.write_text(f"""\
[DEFAULT]'
backend=json
path={json_db}
""")
    return str(happi_cfg_path.absolute())


@pytest.fixture(scope='class')
def json_db(tmp_path_factory):
    dir_path = tmp_path_factory.mktemp("db_dir")
    json_path = dir_path / 'db.json'
    json_path.write_text(json.dumps(ITEMS))
    return str(json_path.absolute())


@pytest.fixture(scope='class')
def items(happi_config):
    client = happi.client.Client.from_config(cfg=happi_config)
    return client.all_items


@pytest.fixture(scope='class')
def raw_items(happi_config):
    client = happi.client.Client.from_config(cfg=happi_config)
    item_list = []
    for item in client.backend.all_devices:
        it = client.find_document(**item)
        item_list.append(it)
    return item_list


@pytest.fixture(scope='class')
def client(happi_config):
    client = happi.client.Client.from_config(cfg=happi_config)
    return client


class TestCommandClass:
    """
    Test that the Command class has been initialized propertly
    And that the abstract classes have raise an error if not implemented
    """
    happi.audit.Command.__abstractmethods__ = set()

    class Dummy(happi.audit.Command):
        pass

    d = Dummy()

    with pytest.raises(NotImplementedError):
        d.add_args('a_parser')
    with pytest.raises(NotImplementedError):
        d.run('some_arg')

    assert isinstance(happi.audit.Command, ABCMeta)


class TestProcessArgs:
    args = argparse.Namespace(cmd='audit', extras=True, path=None,
                              verbose=False, version=False)
    args2 = argparse.Namespace(cmd='audit', extras=False, path=None,
                               verbose=False, version=False)

    def test_check_extra_attributes_called(self):
        with patch('happi.audit.check_extra_attributes') as mock:
            audit.process_database(self.args.extras)
            mock.assert_called_once()

    def test_check_audit_information_from_client_called(self):
        with patch('happi.audit.audit_information_from_client') as mock:
            audit.process_database(self.args2.extras)
            mock.assert_called_once()


class TestValidateRun:
    args = argparse.Namespace(cmd='audit', extras=True, path=None,
                              verbose=False, version=False)

    @patch('happi.audit.process_database')
    def test_process_database_called(self, mock_process_database):
        audit_class.run(self.args)
        mock_process_database.assert_called_once()


class TestValidateContaienr:
    """
    Test the validate_container
    """
    expected = [report_code.INVALID,
                report_code.MISSING,
                report_code.SUCCESS,
                report_code.SUCCESS,
                report_code.SUCCESS]

    def test_validate_container_invalid(self, raw_items):
        res = []
        for item in raw_items:
            audit.validate_container(item)
            res.append(audit.validate_container(item))
        assert res == self.expected


class TestExtraAttributes:
    """
    Test the validate_extra_attributes
    """
    def test_check_extra_attributes(self, client, items):
        calls = []
        for i in items:
            calls.append(call(i))
        with patch('happi.audit.validate_extra_attributes') as m:
            audit.check_extra_attributes(client)
            m.assert_has_calls(calls, any_order=True)

    def test_validate_extra_attributes(self, items):
        for i in items:
            # this item does not have extra items
            if i.name == 'dummy_item':
                res = audit.validate_extra_attributes(i)
                assert res == report_code.SUCCESS
            # this item has extra items
            elif i.name == 'mfx_dg2_ipm':
                res = audit.validate_extra_attributes(i)
                assert res == report_code.EXTRAS


class TestValidateEnforce:
    """
    Testing validate_enforce
    """
    expected = [report_code.MISSING,
                report_code.MISSING,
                report_code.SUCCESS,
                report_code.SUCCESS,
                report_code.INVALID]

    def test_enforce_value(self, raw_items):
        res_list = []
        for item in raw_items:
            res_list.append(audit.validate_enforce(item))
        assert res_list == self.expected


class TestValidateImportClass:
    """
    Testing validate_import_class
    """
    @pytest.fixture(params=[True, False])
    def BOOLEAN(self, request):
        return request.param

    def test_validate_import_class(self, raw_items):
        expected = [report_code.MISSING,
                    report_code.INVALID,
                    report_code.SUCCESS,
                    report_code.SUCCESS,
                    (report_code.INVALID)
                    ]
        res_list = []
        for item in raw_items:
            res_list.append(audit.validate_import_class(item))
        assert res_list == expected


class TestAuditInformationFromClient:
    """
    Simple test to make sure some functions are called
    """
    @patch('happi.client.Client.validate')
    @patch('happi.audit.validate_args')
    @patch('happi.audit.validate_kwargs')
    @patch('happi.audit.validate_enforce')
    @patch('happi.audit.validate_container')
    def test_audit_info_from_client(self, v_c, enf, kwargs, args,
                                    validate, client, items, raw_items):

        v_c_calls = []
        for i in items:
            v_c_calls.append(call(i))
        # should be called 5 time for the 5 items in json_db
        audit.audit_information_from_client(client)

        v_c.assert_called()
        assert v_c.call_count == 5
        enf.assert_called()
        assert enf.call_count == 5

        # the first two items and the last one are malformed
        # so if using:
        # client = Client(path=database_path)
        # items = client.all_items
        # we shuld not be able to get those malformed items
        kwargs.assert_called()
        assert kwargs.call_count == 2
        args.assert_called()
        assert args.call_count == 2

        validate.assert_called_once()
        validate.call_count == 5
