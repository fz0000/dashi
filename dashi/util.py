#!/usr/bin/env python
import json
from ast import literal_eval
from datetime import timedelta
from time import sleep
from urllib.parse import urlparse

import redis
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning


class jenkinsData(object):

    def __init__(self, config):
        disable_warnings(InsecureRequestWarning)
        self.config = config
        self.host = config['host']
        self.user = config['user']
        self.token = config['token']
        self.jobs = config['jobs']
        self.transport = config['transport']
        self.base_url = '%s://%s:%s@%s/' % (self.transport,
                                            self.user,
                                            self.token,
                                            self.host)
        self.data = []

    def lastCompleteBuild(self, job):
        url = '%s/job/%s/lastCompletedBuild/api/json' % (self.base_url, job)
        req = requests.get(url, verify=False)
        if req.status_code == 200:
            data = json.loads(req.text)
            return data
        else:
            return False

    def getTestReport(self, job, buildNum):
        url = '%s/job/%s/%s/testReport/api/json' % (self.base_url, job, buildNum)
        req = requests.get(url, verify=False)
        if req.status_code == 200:
            data = json.loads(req.text)
            return data
        else:
            return False

    def getLastResult(self):
        for jobData in self.jobs:
            job = jobData.get('job')
            shortName = jobData.get('short')
            data = self.lastCompleteBuild(job)
            if data:
                buildUrl = urlparse(data['url'])
                buildLink = '%s://%s%s' % (buildUrl.scheme, self.host, buildUrl.path)
                buildNum = data['number']
                buildResult = data['result']
                buildDurationInSec = (data['duration'] / 1000)
                buildTestReuslt = self.getTestReport(job, buildNum)
                if ((buildResult == 'ABORTED') or (buildResult == 'FAILURE')):
                    if buildTestReuslt:
                        passCount = buildTestReuslt['passCount']
                        failCount = buildTestReuslt['failCount']
                    else:
                        print('no test result found')
                        passCount = 0
                        failCount = 0
                else:
                    if buildTestReuslt:
                        passCount = buildTestReuslt['passCount']
                        failCount = buildTestReuslt['failCount']
                    else:
                        print('no test result found')
                        passCount = 0
                        failCount = 0

                self.data.append(
                    {
                        "name": shortName,
                        "pass": passCount,
                        "fail": failCount,
                        "build": buildNum,
                        "result": buildResult,
                        "buildLink": buildLink,
                        "buildDurationInSec": str(timedelta(seconds=buildDurationInSec))
                    }
                )
        return self.data


def redisPool(config):
    pool = redis.ConnectionPool(
        host=config['redis']['host'],
        port=int(config['redis']['port']),
        db=int(config['redis']['db'])
    )
    return pool


class redisPoller(object):

    def __init__(self, config, redis_pool):
        self.config = config
        self.pool = redis_pool

    def get(self, redis_data_key):
        _redis = redis.Redis(
            connection_pool=self.pool
        )
        try:
            data_ttl = int(_redis.ttl(redis_data_key))
            if data_ttl >= 5:
                data = _redis.get(redis_data_key)
                string_to_dict = literal_eval(data)
                return string_to_dict
            else:
                return False
        except TypeError:
            return False


class jobPoller(object):

    def __init__(self, config, redis_pool):
        self.config = config
        self.redis_expire_time = int(self.config['redis']['expire_time'])
        self.jenkins_poll_interval = int(self.config['poller']['poll_interval'])
        self.pool = redis_pool

    def jenkins(self):
        _redis = redis.Redis(
            connection_pool=self.pool
        )
        while True:
            sleep(self.jenkins_poll_interval)
            result = []
            for host in self.config['jenkins']:
                print('jenkins poll %s' % (host['host']))
                _jenkins_data = jenkinsData(host)
                result.extend(_jenkins_data.getLastResult())

            _redis.set(
                'jenkins-result',
                result,
                ex=self.redis_expire_time
            )
