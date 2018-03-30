import subprocess
import yaml
import boto3
import sys
import os

os.environ['PATH']


def lambda_handler(event, context):
    action = os.environ.get("action")
    cluster_name = 'k8ss8k.io'
    s3_bucket = 'k8ss8k-kops-state'
    s3_key = "k8ss8k.io/instancegroup"
    yes = "--yes"

    if (action == 'start') or (action == "stop"):
        print("{}ing {}".format(action, cluster_name))
    else:
        sys.exit("start and stop actions are only alllowable")

    # desired instance group capacity
    capacity = {
        'masters': (1, ),
        'nodes': (1, 3),
        'bastions': 0
    }

    try:
        boto3.setup_default_session(profile_name=profile)
    except:
        boto3.setup_default_session()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(s3_bucket)

    # download file
    for obj in bucket.objects.filter(Prefix=s3_key):
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
        if action == 'start':
            if file.startswith('master-'):
                group = capacity['masters']
            elif file == 'nodes':
                group = capacity['nodes']
            if len(group) == 1:
                yml['spec']['maxSize'] = group[0]
                yml['spec']['minSize'] = group[0]
            elif len(group) == 2:
                min, max = group
                yml['spec']['maxSize'] = max
                yml['spec']['minSize'] = min
        elif action == 'stop':
            yml['spec']['maxSize'] = 0
            yml['spec']['minSize'] = 0

        # overwrite the S3 file
        data = yaml.dump(yml)
        obj.put(Body=data)

    # update kops cluster
    command = './kops update cluster --name {} --state s3://{} {}'.format(cluster_name, s3_bucket, yes)
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

    # delete temp directory
    if error is None:
        return(output.decode('utf-8'))
    else:
        return(error.decode('utf-8'))


if __name__ == '__main__':
    profile = 'dima'
    s = lambda_handler(None, None)
    print(s)
