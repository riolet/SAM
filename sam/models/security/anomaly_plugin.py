"""
Adaptor/Interface between SAM and security plugin
"""
from datetime import datetime
import logging
from sam.models.subscriptions import Subscriptions
from sam.models.security.alerts import Alerts
from sam.models.security.warnings import Warnings
from sam import errors
logger = logging.getLogger(__name__)

try:
    from security.models import ADELE
    PLUGIN_INSTALLED = True
except:
    PLUGIN_INSTALLED = False


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
        """
        Get new warnings from the plugin and add them into SAM.  No effect if plugin is not installed.
        :param w_model: warning model to insert into
        :type w_model: Warnings
        :return: None
        """
        if not self.adele:
            return
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

    def get_warning(self, warning_id):
        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        return warning

    def get_stats(self):
        if self.status == 'online':
            stats = self.adele.get_stats(self.sub_id)
            return stats
        else:
            return None

    def accept_warning(self, warning_id):
        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        if not warning:
            raise errors.MalformedRequest("unknown warning id")

        # create alert
        alert_model = Alerts(self.db, self.sub_id)
        a_id = alert_model.add_alert(
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

        # push feedback to ADELE if applicable
        if self.adele:
            self.adele.update_warning(self.sub_id, warning_id, 'accepted')
        logger.info("Updating warning {} to be {}".format(warning_id, 'Accepted'))
        return a_id

    def reject_warning(self, warning_id):
        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        if not warning:
            raise errors.MalformedRequest("unknown warning id")
        w_model.update_status(warning_id, 'rejected')

        # push feedback to ADELE
        if self.adele:
            self.adele.update_warning(self.sub_id, warning_id, 'rejected')
        logger.info("Updating warning {} to be {}".format(warning_id, 'Rejected'))

    def ignore_warning(self, warning_id):
        w_model = Warnings(self.db, self.sub_id)
        warning = w_model.get_warning(warning_id)
        if not warning:
            raise errors.MalformedRequest("unknown warning id")
        w_model.update_status(warning_id, 'ignored')

        # push feedback to ADELE
        if self.adele:
            self.adele.update_warning(self.sub_id, warning_id, 'ignored')
        logger.info("Updating warning {} to be {}".format(warning_id, 'Ignored'))
