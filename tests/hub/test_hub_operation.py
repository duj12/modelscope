# Copyright (c) Alibaba, Inc. and its affiliates.
import os
import tempfile
import unittest
import uuid
from shutil import rmtree

from modelscope.hub.api import HubApi, ModelScopeConfig
from modelscope.hub.constants import Licenses, ModelVisibility
from modelscope.hub.file_download import model_file_download
from modelscope.hub.repository import Repository
from modelscope.hub.snapshot_download import snapshot_download

USER_NAME = 'maasadmin'
PASSWORD = '12345678'

model_chinese_name = '达摩卡通化模型'
model_org = 'unittest'
DEFAULT_GIT_PATH = 'git'

download_model_file_name = 'test.bin'


class HubOperationTest(unittest.TestCase):

    def setUp(self):
        self.api = HubApi()
        # note this is temporary before official account management is ready
        self.api.login(USER_NAME, PASSWORD)
        self.model_name = uuid.uuid4().hex
        self.model_id = '%s/%s' % (model_org, self.model_name)
        self.api.create_model(
            model_id=self.model_id,
            visibility=ModelVisibility.PUBLIC,
            license=Licenses.APACHE_V2,
            chinese_name=model_chinese_name,
        )
        temporary_dir = tempfile.mkdtemp()
        self.model_dir = os.path.join(temporary_dir, self.model_name)
        repo = Repository(self.model_dir, clone_from=self.model_id)
        os.system("echo 'testtest'>%s"
                  % os.path.join(self.model_dir, download_model_file_name))
        repo.push('add model')

    def tearDown(self):
        self.api.delete_model(model_id=self.model_id)

    def test_model_repo_creation(self):
        # change to proper model names before use
        try:
            info = self.api.get_model(model_id=self.model_id)
            assert info['Name'] == self.model_name
        except KeyError as ke:
            if ke.args[0] == 'name':
                print(f'model {self.model_name} already exists, ignore')
            else:
                raise

    def test_download_single_file(self):
        downloaded_file = model_file_download(
            model_id=self.model_id, file_path=download_model_file_name)
        assert os.path.exists(downloaded_file)
        mdtime1 = os.path.getmtime(downloaded_file)
        # download again
        downloaded_file = model_file_download(
            model_id=self.model_id, file_path=download_model_file_name)
        mdtime2 = os.path.getmtime(downloaded_file)
        assert mdtime1 == mdtime2

    def test_snapshot_download(self):
        snapshot_path = snapshot_download(model_id=self.model_id)
        downloaded_file_path = os.path.join(snapshot_path,
                                            download_model_file_name)
        assert os.path.exists(downloaded_file_path)
        mdtime1 = os.path.getmtime(downloaded_file_path)
        # download again
        snapshot_path = snapshot_download(model_id=self.model_id)
        mdtime2 = os.path.getmtime(downloaded_file_path)
        assert mdtime1 == mdtime2

    def test_download_public_without_login(self):
        rmtree(ModelScopeConfig.path_credential)
        snapshot_path = snapshot_download(model_id=self.model_id)
        downloaded_file_path = os.path.join(snapshot_path,
                                            download_model_file_name)
        assert os.path.exists(downloaded_file_path)
        temporary_dir = tempfile.mkdtemp()
        downloaded_file = model_file_download(
            model_id=self.model_id,
            file_path=download_model_file_name,
            cache_dir=temporary_dir)
        assert os.path.exists(downloaded_file)
        self.api.login(USER_NAME, PASSWORD)

    def test_snapshot_delete_download_cache_file(self):
        snapshot_path = snapshot_download(model_id=self.model_id)
        downloaded_file_path = os.path.join(snapshot_path,
                                            download_model_file_name)
        assert os.path.exists(downloaded_file_path)
        os.remove(downloaded_file_path)
        # download again in cache
        file_download_path = model_file_download(
            model_id=self.model_id, file_path='README.md')
        assert os.path.exists(file_download_path)
        # deleted file need download again
        file_download_path = model_file_download(
            model_id=self.model_id, file_path=download_model_file_name)
        assert os.path.exists(file_download_path)


if __name__ == '__main__':
    unittest.main()