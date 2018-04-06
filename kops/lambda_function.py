import subprocess
import yaml
import boto3
import sys
import os

os.environ['PATH']


def lambda_handler(event, context):
    try:
        AWS_ACCESS_KEY_ID = event['AWS_ACCESS_KEY_ID'],
        AWS_SECRET_ACCESS_KEY = event['AWS_SECRET_ACCESS_KEY'],
    except:
        pass

    if (event['action'] == 'start') or (event['action'] == "stop"):
        print("{}ing {}".format(event['action'], event['cluster_name']))
    else:
        sys.exit("start and stop actions are only alllowable")

    boto3.setup_default_session()
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(event['s3_bucket'])

    # download file
    for obj in bucket.objects.filter(Prefix=event['s3_key']):
        file = obj.key.split('/')[-1]
        body = obj.get()['Body'].read()
        # change instance group capacity
        try:
            yml = yaml.load(body)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit()
        # delete creationTimestamp key
        try:
            del(yml['metadata']['creationTimestamp'])
        except:
            pass
        if event['action'] == 'start':
            if file.startswith('master-'):
                group = event['capacity']['masters']
            elif file == 'nodes':
                group = event['capacity']['nodes']
            if len(group) == 1:
                yml['spec']['maxSize'] = group[0]
                yml['spec']['minSize'] = group[0]
            elif len(group) == 2:
                min, max = group
                yml['spec']['maxSize'] = max
                yml['spec']['minSize'] = min
        elif event['action'] == 'stop':
            yml['spec']['maxSize'] = 0
            yml['spec']['minSize'] = 0

        # overwrite the S3 file
        data = yaml.dump(yml)
        obj.put(Body=data)

    # update kops cluster
    command = './kops update cluster --name {} --state s3://{} {}'.format(event['cluster_name'], event['s3_bucket'], event['yes'])
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    # delete temp directory
    if error is None:
        return(output.decode('utf-8'))
    else:
        return(error.decode('utf-8'))


if __name__ == '__main__':
    event = {
        "action": "stop",
        "yes": "",
        "capacity": {
            "masters": (1, ),
            "nodes": (1, 3),
            "bastion": (0, )
        },
        # "AWS_ACCESS_KEY_ID": "",
        # "AWS_SECRET_ACCESS_KEY": "",
        "cluster_name": "k8ss8k.io",
        "s3_bucket": "k8ss8k-kops-state",
        "s3_key": "k8ss8k.io/instancegroup"
    }
    s = lambda_handler(event, None)
    print(s)
