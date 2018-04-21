#!/usr/bin/env python3

import boto3
import time


def lambda_handler(event, context):
    cluster = 'k8ss8k.io'
    region = 'us-east-1'
    ts = str(int(round(time.time())))
    filters = [
        {
            'Name': 'tag:KubernetesCluster',
            'Values': [cluster]
        },
        {
            'Name': 'tag:k8s.io/role/master',
            'Values': ['1']
        }
    ]

    ec2 = boto3.resource('ec2', region_name=region)
    volumes = ec2.volumes.filter(Filters=filters)

    for volume in volumes:
        tags = volume.tags
        # add creation timestamp tag
        tags.append(
            {
                'Key': "CreationTimestamp",
                'Value': ts
            }
        )
        snapshot = ec2.create_snapshot(
            Description='{}-etcd-backup'.format(cluster),
            VolumeId=volume.id,
            DryRun=False,
            TagSpecifications=[
                {
                    'ResourceType': 'snapshot',
                    'Tags': tags
                }
            ]
        )
    return 'Hello from Lambda'


if __name__ == "__main__":
    lambda_handler(None, None)
