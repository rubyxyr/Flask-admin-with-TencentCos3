# -*- coding: utf-8 -*-
import os
import time
import os.path as op
from flask_security import current_user
from flask_admin.form import SecureForm
from flask_admin.contrib.fileadmin import BaseFileAdmin
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client


TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', None)
TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', None)
TENCENT_BUCKET = os.getenv('TENCENT_BUCKET', None)
TENCENT_REGION = os.getenv('TENCENT_REGION', None)
TENCENT_BASE_PATH = os.getenv('TENCENT_BASE_PATH', None) # first folder name with slash


class TencentStorage(object):
    def __init__(self, secret_id, secret_key, region, bucket):
        """
        腾讯存储对象管理
        :param secret_id:
        :param secret_key:
        :param region:
        :param bucket: 设置要操作的bucket
        """
        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(config)
        self.bucket = bucket.decode()
        self.client = client
        self.separator = '/'
        self.base_path = TENCENT_BASE_PATH

    def get_files(self, path, directory):
        def _strip_path(name, path):
            if name.startswith(path):
                return name.replace(path, '', 1)
            return name

        def _remove_trailing_slash(raw_name):
            return raw_name[:-1]

        def _iso_to_epoch(timestamp):
            dt = time.strptime(timestamp.split(".")[0], "%Y-%m-%dT%H:%M:%S")
            return int(time.mktime(dt))

        directories = []
        files = []
        prefix = '{0}/'.format(directory)
        path = '{0}/'.format(path)
        response = self.client.list_objects(
            Bucket=self.bucket,
            Prefix=prefix,
            EncodingType='url'
        )

        if 'Contents' in response.keys():
            for _ in response['Contents']:
                if _['Key'].endswith(self.separator):
                    if _['Key'] == prefix:
                        continue
                    name = _remove_trailing_slash(_strip_path(_['Key'], prefix))
                    key_name = _remove_trailing_slash(_strip_path(_['Key'], self.base_path))
                    if '{0}/{1}/'.format(directory, _['Key'].split('/')[-2]) != _['Key']:
                        continue
                    directories.append((name, key_name, True, 0, 0))
                else:
                    name = _strip_path(_['Key'], prefix)
                    key_name = _['Key'].split('/')[-1]
                    if '{0}/{1}'.format(directory, key_name) != _['Key']:
                        continue
                    last_modified = _iso_to_epoch(_['LastModified'])
                    files.append((name, _['Key'].split(self.base_path)[-1], False, _['Size'], last_modified))
        if 'CommonPrefixes' in response.keys():
            for _ in response['CommonPrefixes']:
                name = _remove_trailing_slash(_strip_path(_['Prefix'], path))
                key_name = _remove_trailing_slash(_['Prefix'])
                directories.append((name, key_name, True, 0, 0))
        return directories + files

    def is_dir(self, path):
        if path == '':
            path = TENCENT_BASE_PATH[:-1]
        try:
            response = self.client.list_objects(
                Bucket=self.bucket,
                Prefix='{0}/'.format(path),
                EncodingType='url'
            )
        except:
            return False
        if 'Contents' in response.keys():
            return True
        return False

    def path_exists(self, path):
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=path)
        except:
            try:
                response = self.client.head_object(Bucket=self.bucket, Key='{0}/'.format(path))
            except:
                return False
        return True

    def get_base_path(self):
        return op.normpath(self.base_path)

    def get_breadcrumbs(self, path):
        accumulator = []
        breadcrumbs = []
        for n in path.split(self.separator):
            accumulator.append(n)
            breadcrumbs.append((n, self.separator.join(accumulator)))
        return breadcrumbs

    def send_file(self, file_path):
        pass

    def save_file(self, path, file_data):
        pass

    def delete_tree(self, directory):
        pass

    def delete_file(self, file_path):
        pass

    def make_dir(self, path, directory):
        pass

    def rename_path(self, src, dst):
        pass


class MyBaseForm(SecureForm):
    pass


class TencentFileAdmin(BaseFileAdmin):
    can_download = False
    can_rename = False

    form_base_class = MyBaseForm

    def __init__(self, *args, **kwargs):
        storage = TencentStorage(TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_REGION, TENCENT_BUCKET)
        super(TencentFileAdmin, self).__init__(*args, storage=storage, **kwargs)

    def tencent_opeartion(self, operate, file_type, **kwargs):
        """
        Delete or create file or folder in Tencent COS3
        :param operate: upload or delete
        :param file_type: file or folder
        :return:
        """
        secret_id = TENCENT_SECRET_ID.decode()         # 替换为用户的 secret_id
        secret_key = TENCENT_SECRET_KEY.decode()         # 替换为用户的 secret_key
        region = TENCENT_REGION             # 替换为用户的 region
        bucket = TENCENT_BUCKET.decode()  # 设置要操作的bucket

        config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
        client = CosS3Client(config)
        try:
            if operate == 'upload':
                if file_type == 'file':
                    # upload file
                    filename = kwargs.get('filename', None)
                    response = client.put_object(
                        Bucket=bucket,
                        Body=u'{0}'.format(filename),
                        Key=u'/{0}'.format(filename),
                    )
                else:
                    # upload folder
                    filename = kwargs.get('filename', None)
                    directory = kwargs.get('folder_dir', None)
                    response = client.put_object(
                        Bucket=bucket,
                        Body=u'{0}'.format(filename),
                        Key=u'{0}'.format(directory),
                    )
            else:
                # delete file
                if file_type == 'file':
                    full_path = kwargs.get('full_path', None)
                    response = client.delete_object(
                        Bucket=bucket,
                        Key=u'/{0}'.format(full_path)
                    )
                # delete files
                else:
                    files_list = kwargs.get('files', [])
                    send_data = [{'Key': str(_)} for _ in files_list]
                    response = client.delete_objects(
                        Bucket=bucket,
                        Delete={
                            'Object': send_data,
                            'Quiet': 'false'
                        }
                    )
        except:
            import traceback
            traceback.print_exc()
            return

    def is_accessible(self):
        if not current_user.is_active or not current_user.is_authenticated:
            return False

        if current_user.has_role('superuser') or current_user.has_role('admin'):
            return True

        return False

    def on_file_upload(self, directory, path, filename):
        self.tencent_opeartion('upload', 'file', filename=filename)

    def on_mkdir(self, parent_dir, dir_name):
        folder_dir = '{0}/{1}/'.format(parent_dir, dir_name)
        self.tencent_opeartion('upload', 'folder', filename=dir_name, folder_dir=folder_dir)

    def on_file_delete(self, full_path, filename):
        self.tencent_opeartion('delete', 'file', full_path=full_path)

    def before_directory_delete(self, full_path, dir_name):
        prefix = '{0}/'.format(full_path)
        response = self.storage.client.list_objects(
            Bucket=self.storage.bucket,
            Prefix=prefix,
            EncodingType='url'
        )
        file_list = []
        if 'Contents' in response.keys():
            for _ in response['Contents']:
                file_list.append(_['Key'])
        self.tencent_opeartion('delete', 'folder', files=file_list)
