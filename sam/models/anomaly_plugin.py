"""
Adaptor/Interface between SAM and security plugin
"""
from datetime import datetime
import logging
from sam.models.subscriptions import Subscriptions
from sam.models.alerts import Alerts
from sam.models.warnings import Warnings
from sam import errors
logger = logging.getLogger(__name__)

try:
    from security.models import ADELE
    PLUGIN_INSTALLED = True
except:
    PLUGIN_INSTALLED = False


def import_hook(db, sub_id, ds_id):
    if not PLUGIN_INSTALLED:
        logger.error("Anomaly Detection plugin is missing")
        return
    table = 's{acct}_ds{id}_StagingLinks'.format(acct=sub_id, id=ds_id)
    rows = db.select(table)
    adele = ADELE.Adele(db)
    adele.submit_traffic(sub_id, rows)


class ADPlugin(object):
    def __init__(self, db, sub_id):
        global PLUGIN_INSTALLED
        self.db = db
        self.sub_id = sub_id
        self.plugin_name = "A.D.E.L.E."
        if PLUGIN_INSTALLED:
            self.status = ADELE.Adele.get_status()
            self.adele = ADELE.Adele(self.db)
        else:
            self.status = 'unavailable'
            self.adele = None

    def get_status(self):
        if PLUGIN_INSTALLED:
            self.status = ADELE.Adele.get_status()
        return self.status

    def get_active(self):
        sub_model = Subscriptions(self.db)
        p_data = sub_model.get_plugin_data(self.sub_id, 'ADPlugin')
        active = p_data.get('active', True)
        return active

    def enable(self):
        # save in local plugin settings
        sub_model = Subscriptions(self.db)
        sub_model.set_plugin_data(self.sub_id, 'ADPlugin', {'active': True})
        logger.info("Setting processor ON")

    def disable(self):
        # save in local plugin settings
        sub_model = Subscriptions(self.db)
        sub_model.set_plugin_data(self.sub_id, 'ADPlugin', {'active': False})
        logger.info("Setting processor OFF")

    def _retrieve_warnings(self, w_model):
        latest = w_model.get_latest_warning_id()
        new_warnings = self.adele.get_warnings(self.sub_id, latest)
        if new_warnings:
            w_model.insert_warnings(new_warnings)

    def get_warnings(self, show_all=False):
        w_model = Warnings(self.db, self.sub_id)
        if self.status == 'online':
            self._retrieve_warnings(w_model)
        wlist = w_model.get_warnings(show_all=show_all)
        return wlist

    def get_stats(self):
        if self.status == 'online':
            stats = self.adele.get_stats(self.sub_id)
            return stats
        else:
            return None

    def accept_warning(self, warning_id):
        if self.status != 'online':
            return

        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        if not warning:
            raise errors.MalformedRequest("unknown warning id")

        # create alert
        alert_model = Alerts(self.db, self.sub_id)
        alert_model.add_alert(
            ipstart=warning['host'],
            ipend=warning['host'],
            severity=5,
            rule_id=None,
            rule_name=self.plugin_name,
            label=warning['reason'],
            details=warning['details'],
            timestamp=datetime.fromtimestamp(warning['log_time']))
        # update local table
        w_model.update_status(warning_id, 'accepted')

        # push feedback to ADELE
        self.adele.update_warning(self.sub_id, warning_id, 'accepted')
        logger.info("Updating warning {} to be {}".format(warning_id, 'Accepted'))

    def reject_warning(self, warning_id):
        if self.status != 'online':
            return

        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        if not warning:
            raise errors.MalformedRequest("unknown warning id")
        w_model.update_status(warning_id, 'rejected')

        # push feedback to ADELE
        self.adele.update_warning(self.sub_id, warning_id, 'rejected')
        logger.info("Updating warning {} to be {}".format(warning_id, 'Rejected'))

    def ignore_warning(self, warning_id):
        if self.status != 'online':
            return

        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        if not warning:
            raise errors.MalformedRequest("unknown warning id")
        w_model.update_status(warning_id, 'ignored')

        # push feedback to ADELE
        self.adele.update_warning(self.sub_id, warning_id, 'ignored')
        logger.info("Updating warning {} to be {}".format(warning_id, 'Ignored'))

    def reset_all_profiles(self):
        if self.status != 'online':
            return

        self.adele.reset_all_profiles()
        logger.info("Cleared all profile data")

    def reset_profile(self, host_ip):
        if self.status != 'online':
            return

        self.adele.reset_profile(host_ip)
        logger.info("Cleared profile of {}".format(host_ip))

    def submit_traffic(self, traffic, _category="unknown"):
        if self.status != 'online':
            return

        if _category == 'ignored':
            logger.debug('Adding ignored traffic: {}...'.format(repr(traffic)[:50]))
            logger.warning('Adding pre-ignored traffic will do nothing.')
        elif _category == 'good':
            logger.debug('Adding healthy traffic: {}...'.format(repr(traffic)[:50]))
            self.adele.submit_traffic(self.sub_id, traffic, _category=_category)
        elif _category == 'bad':
            logger.debug("Adding known bad traffic: {}...".format(repr(traffic)[:50]))
            self.adele.submit_traffic(self.sub_id, traffic, _category=_category)
        else:
            logger.debug('Adding undetermined traffic: {}...'.format(repr(traffic)[:50]))
            self.adele.submit_traffic(self.sub_id, traffic, _category=_category)
