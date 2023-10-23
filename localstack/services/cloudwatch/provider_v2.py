import logging

from localstack.aws.api import RequestContext, handler
from localstack.aws.api.cloudwatch import (
    ActionPrefix,
    AlarmArn,
    AlarmName,
    AlarmNamePrefix,
    AlarmNames,
    AlarmTypes,
    CloudwatchApi,
    DescribeAlarmsOutput,
    MaxRecords,
    NextToken,
    PutMetricAlarmInput,
    StateValue,
)
from localstack.deprecations import deprecated_endpoint
from localstack.services.cloudwatch.alarm_scheduler import AlarmScheduler
from localstack.services.cloudwatch.models import CloudWatchStore, cloudwatch_stores
from localstack.services.edge import ROUTER
from localstack.services.plugins import SERVICE_PLUGINS, ServiceLifecycleHook
from localstack.utils.sync import poll_condition
from localstack.utils.tagging import TaggingService
from localstack.utils.threads import start_worker_thread

PATH_GET_RAW_METRICS = "/_aws/cloudwatch/metrics/raw"
DEPRECATED_PATH_GET_RAW_METRICS = "/cloudwatch/metrics/raw"
MOTO_INITIAL_UNCHECKED_REASON = "Unchecked: Initial alarm creation"

LOG = logging.getLogger(__name__)


class CloudwatchProvider(CloudwatchApi, ServiceLifecycleHook):
    """
    Cloudwatch provider.

    LIMITATIONS:
        - no alarm rule evaluation
    """

    def __init__(self):
        self.tags = TaggingService()
        self.alarm_scheduler: AlarmScheduler = None
        self.store = None

    @staticmethod
    def get_store(account_id: str, region: str) -> CloudWatchStore:
        return cloudwatch_stores[account_id][region]

    @staticmethod
    def get_alarm_arn(account_id: str, region: str, name: str) -> AlarmArn:
        # TODO: move this to the data class of Alarm should we introduce one
        return f"arn:aws:sqs:{region}:{account_id}:{name}"

    def on_after_init(self):
        ROUTER.add(PATH_GET_RAW_METRICS, self.get_raw_metrics)
        # TODO remove with 2.0
        ROUTER.add(
            DEPRECATED_PATH_GET_RAW_METRICS,
            deprecated_endpoint(
                self.get_raw_metrics,
                previous_path=DEPRECATED_PATH_GET_RAW_METRICS,
                deprecation_version="1.3.0",
                new_path=PATH_GET_RAW_METRICS,
            ),
        )
        self.start_alarm_scheduler()

    def on_before_state_reset(self):
        self.shutdown_alarm_scheduler()

    def on_after_state_reset(self):
        self.start_alarm_scheduler()

    def on_before_state_load(self):
        self.shutdown_alarm_scheduler()

    def on_after_state_load(self):
        self.start_alarm_scheduler()

        def restart_alarms(*args):
            poll_condition(lambda: SERVICE_PLUGINS.is_running("cloudwatch"))
            self.alarm_scheduler.restart_existing_alarms()

        start_worker_thread(restart_alarms)

    def on_before_stop(self):
        self.shutdown_alarm_scheduler()

    def start_alarm_scheduler(self):
        if not self.alarm_scheduler:
            LOG.debug("starting cloudwatch scheduler")
            self.alarm_scheduler = AlarmScheduler()

    def shutdown_alarm_scheduler(self):
        LOG.debug("stopping cloudwatch scheduler")
        self.alarm_scheduler.shutdown_scheduler()
        self.alarm_scheduler = None

    def delete_alarms(self, context: RequestContext, alarm_names: AlarmNames) -> None:
        """
        Delete alarms.
        """

        for alarm_name in alarm_names.alarm_names:
            alarm_arn = ""  # obtain alarm ARN from alarm name
            self.alarm_scheduler.delete_alarm(alarm_arn)

    @handler("PutMetricAlarm", expand=False)
    def put_metric_alarm(self, context: RequestContext, request: PutMetricAlarmInput) -> None:

        store = self.get_store(context.account_id, context.region)
        alarm = {**request}
        alarm_arn = self.get_alarm_arn(context.account_id, context.region, request.get("AlarmName"))
        store.Alarms[alarm_arn] = alarm

    def describe_alarms(
        self,
        context: RequestContext,
        alarm_names: AlarmNames = None,
        alarm_name_prefix: AlarmNamePrefix = None,
        alarm_types: AlarmTypes = None,
        children_of_alarm_name: AlarmName = None,
        parents_of_alarm_name: AlarmName = None,
        state_value: StateValue = None,
        action_prefix: ActionPrefix = None,
        max_records: MaxRecords = None,
        next_token: NextToken = None,
    ) -> DescribeAlarmsOutput:
        store = self.get_store(context.account_id, context.region)
        composite_alarms = []
        metric_alarms = []
        for alarm_arn, alarm in store.Alarms.items():
            alarm["AlarmArn"] = alarm_arn
            metric_alarms.append(alarm)
        return DescribeAlarmsOutput(CompositeAlarms=composite_alarms, MetricAlarms=metric_alarms)
