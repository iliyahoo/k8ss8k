#!/usr/bin/env python3

import boto3


def lambda_handler(event, context):
    cluster = event['cluster']
    region = event['region']
    CreationTimestamp = event['CreationTimestamp']
    filters = [
        {
            'Name': 'tag:KubernetesCluster',
            'Values': [cluster]
        },
        {
            'Name': 'tag:CreationTimestamp',
            'Values': [CreationTimestamp]
        }
    ]

    ec2 = boto3.resource('ec2', region_name=region)

    snapshots = ec2.snapshots.filter(
        Filters=filters
    )

    for snapshot in snapshots:
        tags = snapshot.tags
        # find out AZ
        for tag in tags:
            if tag['Key'] == 'Name':
                region_zone = region + tag['Value'].split('.')[0]
                break
        # restore volume
        volume = ec2.create_volume(
            AvailabilityZone=region_zone,
            Encrypted=False,
            SnapshotId=snapshot.id,
            VolumeType='gp2',
            TagSpecifications=[
                {
                    'ResourceType': 'volume',
                    'Tags': tags
                },
            ]
        )
    return 'Hello from Lambda'


if __name__ == "__main__":
    event = {
        "cluster": "k8ss8k.io",
        "region": "us-east-1",
        "CreationTimestamp": "1524258983"
    }
    lambda_handler(event, None)
