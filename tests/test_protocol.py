"""
Test the FRAME/UNFRAME functions in the sequence expected from ziplines.
"""
import pytz

from unittest2 import TestCase
from datetime import datetime, timedelta
from collections import defaultdict

from nose.tools import timed

import zipline.utils.factory as factory
from zipline.utils import logger
import zipline.protocol as zp

from zipline.finance.sources import SpecificEquityTrades

DEFAULT_TIMEOUT = 5 # seconds

class ProtocolTestCase(TestCase):

    leased_sockets = defaultdict(list)

    def setUp(self):
        #qutil.configure_logging()
        self.trading_environment = factory.create_trading_environment()

    @timed(DEFAULT_TIMEOUT)
    def test_trade_feed_protocol(self):

        sid = 133
        price = [10.0] * 4
        volume = [100] * 4

        start_date = datetime.strptime("02/15/2012","%m/%d/%Y")
        one_day_td = timedelta(days=1)

        trades = factory.create_trade_history(
            sid,
            price,
            volume,
            one_day_td,
            self.trading_environment
        )

        for trade in trades:
            #simulate data source sending frame
            msg = zp.DATASOURCE_FRAME(zp.ndict(trade))
            #feed unpacking frame
            recovered_trade = zp.DATASOURCE_UNFRAME(msg)
            #feed sending frame
            feed_msg = zp.FEED_FRAME(recovered_trade)
            #transform unframing
            recovered_feed = zp.FEED_UNFRAME(feed_msg)
            #do a transform
            trans_msg = zp.TRANSFORM_FRAME('helloworld', 2345.6)
            #simulate passthrough transform -- passthrough shouldn't even
            # unpack the msg, just resend.

            passthrough_msg = zp.TRANSFORM_FRAME(zp.TRANSFORM_TYPE.PASSTHROUGH,\
                    feed_msg)

            #merge unframes transform and passthrough
            trans_recovered = zp.TRANSFORM_UNFRAME(trans_msg)
            pt_recovered = zp.TRANSFORM_UNFRAME(passthrough_msg)
            #simulated merge
            pt_recovered.PASSTHROUGH.merge(trans_recovered)
            #frame the merged event
            merged_msg = zp.MERGE_FRAME(pt_recovered.PASSTHROUGH)
            #unframe the merge and validate values
            event = zp.MERGE_UNFRAME(merged_msg)

            #check the transformed value, should only be in event, not trade.
            self.assertTrue(event.helloworld == 2345.6)
            event.delete('helloworld')

            self.assertEqual(zp.ndict(trade), event)