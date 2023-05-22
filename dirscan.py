import os
import time
import threading
import requests
import argparse
import random
import datetime
from lib import generate
from lib import datarecorder
from termcolor import cprint
from urllib.parse import urlparse


class Dirscan:
    def __init__(self, url, threads, extensions, status_codes):
        self.url = url
        self.threads = threads
        self.extensions = extensions
        self.status_codes = self.expand_status_codes(status_codes)
        self.dictionary = self.load_dictionary()
        self.scan_list = [self.url]
        self.results = []  # 存储扫描结果的列表
        self.last_timestamp = None  # 上一次使用的时间戳
        self.total_requests = 0
        self.lock = threading.Lock()
        print()

    def expand_status_codes(self, status_codes):
        expanded_status_codes = set()

        for code in status_codes:
            if "-" in code:
                start, end = map(int, code.split("-"))
                expanded_status_codes.update(range(start, end + 1))
            else:
                expanded_status_codes.add(int(code))

        return expanded_status_codes

    def load_dictionary(self):
        with open("./config/dicts.txt",encoding="utf-8",mode="r") as f:
            return f.read().splitlines()

    def get_random_user_agent(self):
        with open("./config/user-agents.txt",encoding="utf-8",mode="r") as f:
            return random.choice(f.read().splitlines())

    def worker(self):
        while True:
            url = self.get_next_url()
            if url is None:
                break

            self.scan_directory(url)

    def scan_directory(self, url):
        url = url.rstrip("/")
        for directory in self.dictionary:
            directory_url = f"{url}/{directory.lower()}/"
            self.scan_url(directory_url)

            for extension in self.extensions:
                file_url = f"{url}/{directory.lower()}.{extension}"
                self.scan_url(file_url)

    def format_size(self, size):
        suffixes = ["B", "KB", "MB", "GB"]
        for suffix in suffixes:
            if size < 1024:
                return f"{size:.2f}{suffix}"
            size /= 1024

    def scan_url(self, url):
        try:
            with self.lock:
                self.total_requests += 1
            headers = {"User-Agent": self.get_random_user_agent()}
            response = requests.get(url, headers=headers, timeout=3)
            status_code = response.status_code
            if status_code in self.status_codes:
                content_length = response.headers.get("Content-Length", 0)
                content_length_formatted = self.format_size(int(content_length))
                color = "green" if status_code == 200 else "blue" if status_code == 302 else "yellow"
                with self.lock:
                    if url not in self.scan_list:
                        cprint(f"[+] Found: [{status_code}] [{content_length_formatted}] {url}", color)
                        self.scan_list.append(url)
                        self.results.append({
                            "url": url,
                            "status": status_code,
                            "contentLength": content_length_formatted
                        })
                        self.save_html()
                        self.save_datarecorder(url)
        except requests.exceptions.RequestException as e:
            # cprint(f"[-] Request Exception occurred for URL: {url}", "red")
            # print(e)
            pass

    def get_next_url(self):
        with self.lock:
            if self.scan_list:
                return self.scan_list.pop(0)
        return None

    def start_scan(self):
        start_time = time.time()

        threads = [threading.Thread(target=self.worker) for _ in range(self.threads)]
        for t in threads:
            t.start()

        while any(thread.is_alive() for thread in threads):
            time.sleep(0.1)
            with self.lock:
                total_requests = self.total_requests
            print(f"\rTotal Requests: {total_requests}\r", end="")

        elapsed_time = time.time() - start_time
        print(f"\nElapsed Time: {elapsed_time:.2f}s")

    def save_html(self):
        parsed_url = urlparse(self.url)
        netloc = parsed_url.netloc
        now = datetime.datetime.now()
        if self.last_timestamp:
            timestamp = self.last_timestamp
        else:
            timestamp = now.strftime("%Y%m%d%H%M%S")
            self.last_timestamp = timestamp
        directory = "./results"
        os.makedirs(directory, exist_ok=True)
        filename = f"{directory}/{netloc}_{timestamp}.html"

        html = generate.generate_html(self.results)
        with open(filename, "w") as f:
            f.write(html)

    def save_datarecorder(self, url):
        recorder = datarecorder.DataRecorder("./config/dicts_record.txt")
        last_part = os.path.splitext(os.path.basename(url.rstrip("/")))[0]
        recorder.add_data(last_part)
        recorder.save_to_file()

    def add_parent_urls(self, url):
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        netloc = parsed_url.netloc
        path = parsed_url.path.strip("/")
        parent_paths = [f"{scheme}://{netloc}"]
        for part in path.split("/"):
            if part:
                parent_paths.append(f"{parent_paths[-1]}/{part}")
        self.scan_list.extend(parent_paths)

def parser_cprint(threads, extensions,status_codes):
    cprint(f"Threads: {threads}", "yellow")
    cprint(f"Extensions: {', '.join(extensions)}", "yellow")
    cprint(f"Status Codes: {status_codes}", "yellow")

def url_split(url):
    if '.' in url:
        url = url.rsplit('/', 1)[0]
    return url

def main():
    parser = argparse.ArgumentParser(description="Multi-threaded web directory scanner")
    parser.add_argument("-u", "--url", help="URL of the target website")
    parser.add_argument("-f", "--file", help="URLs.txt of the target website")
    parser.add_argument("-t", "--threads", type=int, default=20, help="Number of threads (default: %(default)s)")
    parser.add_argument("-e", "--extensions", default="jsp,php,asp,aspx,zip,rar,7z,tar,tar.gz,bak,old",
                        help="Extensions to append to URLs (default: %(default)s)")
    parser.add_argument("--status-codes", nargs="+", default=["200-399", "401", "403", "405"],
                        help="Allowed HTTP status codes (default: %(default)s)")

    args = parser.parse_args()
    extensions = args.extensions.split(",")
    status_codes = args.status_codes

    if args.url:
        args.url = url_split(args.url)
        parser_cprint(args.threads, extensions,status_codes)
        cprint(f"Target URL: {args.url}", "yellow")
        scanner = Dirscan(args.url, args.threads, extensions, status_codes)
        scanner.add_parent_urls(args.url)
        scanner.start_scan()
    elif args.file:
        parser_cprint(args.threads, extensions,status_codes)
        urls = open(args.file,encoding="utf-8",mode="r")
        for url in urls:
            args.url = url.rstrip('\n')
            if args.url:
                args.url = url_split(args.url)
                cprint(f"Target URL: {args.url}", "yellow")
                scanner = Dirscan(args.url, args.threads, extensions, status_codes)
                scanner.add_parent_urls(args.url)
                scanner.start_scan()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
