import json
import os
import shutil
import subprocess
import tarfile
import sys
import time
import signal
try:
    from urllib2 import urlopen, URLError, HTTPError
except BaseException:
    from urllib.request import urlopen, URLError, HTTPError

# models from onnx-mxnet model zoo
onnx_model_urls = {
    'bvlc_alexnet': 'https://s3.amazonaws.com/download.onnx/models/bvlc_alexnet.tar.gz',
    'densenet121': 'https://s3.amazonaws.com/download.onnx/models/densenet121.tar.gz',
    'inception_v1': 'https://s3.amazonaws.com/download.onnx/models/inception_v1.tar.gz',
    'inception_v2': 'https://s3.amazonaws.com/download.onnx/models/inception_v2.tar.gz',
    'resnet50': 'https://s3.amazonaws.com/download.onnx/models/resnet50.tar.gz',
    'shufflenet': 'https://s3.amazonaws.com/download.onnx/models/shufflenet.tar.gz',
    'squeezenet': 'https://s3.amazonaws.com/download.onnx/models/squeezenet.tar.gz',
    'vgg16': 'https://s3.amazonaws.com/download.onnx/models/vgg16.tar.gz',
    'vgg19': 'https://s3.amazonaws.com/download.onnx/models/vgg19.tar.gz'}

# models from onnx-mxnet model zoo
onnx_mxnet_model_urls = {
    'onnx-alexnet': 'https://s3.amazonaws.com/model-server/models/onnx-alexnet/alexnet.onnx',
    'onnx-squeezenet': 'https://s3.amazonaws.com/model-server/models/onnx-squeezenet/squeezenet.onnx',
    'onnx-inception_v1': 'https://s3.amazonaws.com/model-server/models/onnx-inception_v1/inception_v1.onnx',
    'onnx-vgg19': 'https://s3.amazonaws.com/model-server/models/onnx-vgg19/vgg19.onnx'}

# models from onnx-mxnet model zoo
mxnet_model_urls = {
    # TODO: check why these two models are failing github issue #345
    'caffenet': 'https://s3.amazonaws.com/model-server/models/caffenet/caffenet.model',
    'Inception-BN': 'https://s3.amazonaws.com/model-server/models/inception-bn/Inception-BN.model',
    # 'lstm_ptb'        : 'https://s3.amazonaws.com/model-server/models/lstm_ptb/lstm_ptb.model',
    'nin': 'https://s3.amazonaws.com/model-server/models/nin/nin.model',
    'resnet-152': 'https://s3.amazonaws.com/model-server/models/resnet-152/resnet-152.model',
    'resnet-18': 'https://s3.amazonaws.com/model-server/models/resnet-18/resnet-18.model',
    # 'resnet50_ssd_model'    : 'https://s3.amazonaws.com/model-server/models/resnet50_ssd/resnet50_ssd_model.model',
    'resnext-101-64x4d': 'https://s3.amazonaws.com/model-server/models/resnext-101-64x4d/resnext-101-64x4d.model',
    'squeezenet_v1.1': 'https://s3.amazonaws.com/model-server/models/squeezenet_v1.1/squeezenet_v1.1.model',
    'vgg19': 'https://s3.amazonaws.com/model-server/models/vgg19/vgg19.model',
}


def filtered_urls(model_list, url):
    filtered_url = {}
    for models in model_list:
        filtered_url[models] = url[models]
    return filtered_url


def _download_file(download_dir, url):
    """
        Helper function to download the file from specified url
    :param url: File to download
    :return: None
    """
    try:
        f = urlopen(url)
        print("Downloading - {}".format(url))
        with open(os.path.join(download_dir, os.path.basename(url)), "wb") as local_file:
            local_file.write(f.read())
    except HTTPError as e:
        print("Failed to download {}. HTTP Error {}".format(url, e.code))
    except URLError as e:
        print("Failed to download {}. HTTP Error {}".format(url, e.reason))


def cleanup(tmpdir):
    print("Deleting all downloaded resources for SSD MXNet Model Server Integration Test")
    shutil.rmtree(str(tmpdir))


def create_model_onnx_zoo(download_dir, url, onnx_model):
    _download_file(download_dir, url[onnx_model])
    _download_file(
        download_dir,
        "https://s3.amazonaws.com/model-server/models/onnx-squeezenet/signature.json")
    _download_file(
        download_dir,
        "https://s3.amazonaws.com/model-server/models/onnx-squeezenet/synset.txt")
    model_tar = '{}/{}.tar.gz'.format(download_dir, onnx_model)
    tar = tarfile.open(model_tar, "r:*")
    tar.extractall(path=download_dir)
    tar.close()
    model_dir = '{}/{}'.format(download_dir, onnx_model)
    model_path = os.path.join(model_dir, 'model.onnx')
    new_path = os.path.join(
        model_dir, '{}.onnx'.format(onnx_model))
    os.rename(model_path, new_path)
    shutil.move(new_path, download_dir)


def create_model_onnx_mxnet_zoo(download_dir, url, onnx_model):
    _download_file(download_dir, url[onnx_model])
    _download_file(
        download_dir,
        "https://s3.amazonaws.com/model-server/models/" +
        onnx_model +
        "/signature.json")
    _download_file(
        download_dir,
        "https://s3.amazonaws.com/model-server/models/" +
        onnx_model +
        "/synset.txt")


def export_onnx_models(tmpdir, onnx_source_model_zoo, url, onnx_model):
    download_dir = tmpdir + '/mxnet_model_server'
    os.mkdir(download_dir)
    if onnx_source_model_zoo:
        create_model_onnx_zoo(download_dir, url, onnx_model)
    else:
        create_model_onnx_mxnet_zoo(download_dir, url, onnx_model)

    print('model files prepared for model {} '.format(onnx_model))
    # Export the model.
    print("Exporting the mxnet model server model...")
    subprocess.check_call(['mxnet-model-export',
                           '--model-name',
                           onnx_model,
                           '--model-path',
                           download_dir],
                          cwd=download_dir)
    shutil.move('{}/{}.model'.format(download_dir, onnx_model), tmpdir)
    for root, dirs, files in os.walk(download_dir):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
    shutil.rmtree(download_dir)


def create_model(
        tmpdir,
        url,
        onnx_model,
        onnx_source_model_zoo=True,
        is_onnx_model=True):
    # Download the files required for onnx integ tests.
    try:
        if is_onnx_model:
            export_onnx_models(tmpdir, onnx_source_model_zoo, url, onnx_model)
        else:
            _download_file(tmpdir, url[onnx_model])
    except Exception as e:
        print("Failed to create models. {}".format(str(e)))
        raise


def start_test(
        tmpdir,
        url,
        port='8080',
        onnx_source_model_zoo=False,
        is_onnx_model=True):
    model_list = []
    model_names = []
    for model in url.keys():
        create_model(
            tmpdir,
            url,
            model,
            onnx_source_model_zoo,
            is_onnx_model)
        model_names.append('{}={}/{}.model'.format(model, tmpdir, model))
        model_list.append(model)
    server_pid = subprocess.Popen(
        ['mxnet-model-server', '--models'] + model_names + ['--port', port]).pid

    try:
        time.sleep(30)
        if is_onnx_model:
            data_name = 'input_0'
        else:
            data_name = 'data'
        for models in model_list:
            output = subprocess.check_output(['curl',
                                              '-X',
                                              'POST',
                                              'http://127.0.0.1:' + port + '/' + models + '/predict',
                                              '-F',
                                              '{}=@{}/kitten.jpg'.format(data_name,
                                                                         tmpdir)])
            if sys.version_info[0] >= 3:
                output = output.decode("utf-8")
            predictions = json.dumps(json.loads(output))
            # Assert objects are detected.
            assert predictions is not None
            assert len(predictions) > 0
    except Exception as e:
        print("Failed to test models. {} ".format(str(e)))
        raise
    finally:
        os.kill(server_pid, signal.SIGQUIT)
