from time import time
from collections import deque
from threading import RLock, Thread
from random import Random
from httplib import HTTPConnection
from argparse import ArgumentParser


class RWF:

    def __init__(self, num_threads=30, conn_timeout=1,
                 sec_limit=None, min_limit=None, hour_limit=None,
                 site_limit=None, addrs_limit=None):
        self.num_threads = num_threads
        self.conn_timeout = conn_timeout
        self.start_time = None
        self.limits = {}
        self.limits["user"] = False
        self.limits["time"] = {"sec": sec_limit, "min": min_limit,
                               "hour": hour_limit}
        self.limits["time"]["total"] = self.time_limit()
        self.limits["site"] = site_limit
        self.limits["addrs"] = addrs_limit
        self.num_addrs_tested = 0
        self.num_addrs_tested_lock = RLock()
        self.num_sites_found = 0
        self.num_sites_found_lock = RLock()
        self.threads = []
        self.sites = deque()

    @classmethod
    def from_cmdline(cls):
        finder_parser = RWFArgParser()
        args_dict = vars(finder_parser.parse_args())
        return cls(**args_dict)

    def time_limit(self):
        total = 0
        multiples = {"sec": 1, "min": 60, "hour": 60**2}
        for key, value in self.limits["time"].iteritems():
            if value is not None:
                total += (value * multiples[key])
        if total == 0:
            return None
        else:
            return total

    def limited(self):
        time_limited = self.limits["time"]["total"] is not None
        site_limited = self.limits["site"] is not None
        addrs_limited = self.limits["addrs"] is not None
        with self.num_addrs_tested_lock:
            at_addrs_tested_lim = self.num_addrs_tested >= self.limits["addrs"]
        if ((time_limited and self.remaining_time() <= 0) or
           (site_limited and self.num_sites_found >= self.site_limit) or
           (addrs_limited and at_addrs_tested_lim) or
           (self.limits["user"])):
            return True
        else:
            return False

    def remaining_time(self):
        current_time = time()
        running_time = current_time - self.start_time
        remaining_time = self.limits["time"]["total"] - running_time
        return remaining_time

    def random_addrs(self):
        addrs = []
        total_range = xrange(0, 256)
        # addresses not routed on the public internet
        # http://en.wikipedia.org/wiki/Reserved_IP_addresses
        # the key is the address element previously generated and
        # the value is a range of values the next element can't be
        # "all" refers to all element values in that location
        options = {"all": [0, 10, 127] + range(224, 256),
                   100: {"all": xrange(64, 128)},
                   169: {"all": [254]},
                   172: {"all": xrange(16, 32)},
                   192: {"all": [168],
                         0: {"all": [2],
                             0: xrange(0, 8)}
                         },
                   198: {"all": [18, 20],
                         51: [100]
                         },
                   203: {"all": [],
                         0: [113]
                         }
                   }
        self.use_options(options, addrs, total_range)
        return "{}.{}.{}.{}".format(*addrs)

    def use_options(self, location, addrs, total_range):
        rand = Random()
        if len(addrs) < 4:
            # get list of the next part of the addrs that is not routed
            # based on the location(addrs part number and previous addrses)
            if type(location) == dict:
                not_routed = location["all"]
            elif type(location) == list:
                not_routed = location
            # perform set difference on the list and total_range to
            # get an addrs element, then append
            addrs.append(rand.choice(self.list_diff(total_range, not_routed)))
            # if location is a dict, change location to the value for the
            # key in the dict that equals the last element of addrs
            if type(location) == dict:
                if addrs[-1] in location.keys():
                    location = location[addrs[-1]]
            # if location is a list, there are no more nested dicts, so choose
            # next addrs element from whole range
            elif type(location) == list:
                addrs.append(rand.choice(total_range))
            # calls use_options again until there are four elements
            self.use_options(location, addrs, total_range)
        # four elements, addrs completed
        else:
            pass

    @staticmethod
    def list_diff(minuend, subtrahend):
        return list(set(minuend) - set(subtrahend))

    def is_site(self, addrs):
        with self.num_addrs_tested_lock:
            self.num_addrs_tested += 1
        try:
            conn = HTTPConnection(addrs, timeout=self.conn_timeout)
            conn.request("HEAD", "/")
            status = conn.getresponse().status
            if status in [200]:
                return True
            else:
                return False
        except:
            return False

    def find_sites(self):
        while not self.limited():
            addrs = self.random_addrs()
            if self.is_site(addrs):
                with self.num_sites_found_lock:
                    self.num_sites_found += 1
                self.sites.append(addrs)

    def start_finding(self):
        self.limits["user"] = False
        self.start_time = time()
        for i in range(self.num_threads):
            thread = Thread(target=self.find_sites)
            thread.start()
            self.threads.append(thread)

    def stop_finding(self):
        self.limits["user"] = True


class RWFArgParser(ArgumentParser):

    def __init__(self):
        super(RWFArgParser, self).__init__(description="Random Website Finder")

    def parse_args(self):
        super(RWFArgParser, self).add_argument(
            "-th", "--num-threads",
            type=int, help="set the number of website finding threads")
        super(RWFArgParser, self).add_argument(
            "-ct", "--conn-timeout", type=int,
            help=("set the maximum amount of seconds "
                  "to attempt to connect to addresses"))
        super(RWFArgParser, self).add_argument(
            "-sec", "--sec-limit", type=int,
            help="set an amount of seconds to add to the runtime")
        super(RWFArgParser, self).add_argument(
            "-min", "--min-limit", type=int,
            help="set an amount of minutes to add to the runtime")
        super(RWFArgParser, self).add_argument(
            "-hr", "--hour-limit", type=int,
            help="set an amount of hours to add to the runtime")
        super(RWFArgParser, self).add_argument(
            "-e", "--site-limit", type=int,
            help=("set an amount of sites, that when "
                  "found will cause finding to stop"))
        super(RWFArgParser, self).add_argument(
            "-a", "--addrs-limit", type=int,
            help="set an amount of addresses tested to limit the runtime")
        super(RWFArgParser, self).set_defaults(num_threads=30, conn_timeout=1)
        args = super(RWFArgParser, self).parse_args()
        if not (args.sec_limit or args.min_limit or args.hour_limit):
            super(RWFArgParser, self).error(
                ("At least one of --sec-limit, --min-limit, --hour-limit, \n"
                 "--addrs-limit, or site-limit arguments must be given"))
        return args


def main():
    finder = RWF.from_cmdline()
    finder.start_finding()
    while not finder.limited():
        if len(finder.sites) > 0:
            print finder.sites.pop()

if __name__ == "__main__":
    main()
