#!/usr/bin/env python3
"""Dependency-free live system monitor for Linux terminals."""

import argparse
import curses
import json
import os
import shutil
import time


def cpu_times():
	with open("/proc/stat", encoding="ascii") as file:
		return [int(value) for value in file.readline().split()[1:]]


def cpu_usage(previous, current):
	total = sum(current) - sum(previous)
	idle = current[3] - previous[3]
	return 0.0 if total <= 0 else max(0.0, min(100.0, 100 * (1 - idle / total)))


def memory_info():
	values = {}
	with open("/proc/meminfo", encoding="ascii") as file:
		for line in file:
			name, value, *_ = line.split()
			values[name.rstrip(":")] = int(value) * 1024
	total = values.get("MemTotal", 0)
	available = values.get("MemAvailable", values.get("MemFree", 0))
	return {"total": total, "used": max(0, total - available), "available": available}


def network_bytes():
	received = sent = 0
	with open("/proc/net/dev", encoding="ascii") as file:
		for line in file:
			if ":" not in line:
				continue
			interface, data = line.split(":", 1)
			if interface.strip() == "lo":
				continue
			columns = data.split()
			received += int(columns[0])
			sent += int(columns[8])
	return received, sent


def processes():
	result = []
	for entry in os.scandir("/proc"):
		if not entry.name.isdigit():
			continue
		try:
			with open(f"/proc/{entry.name}/stat", encoding="ascii") as file:
				fields = file.read().split()
			with open(f"/proc/{entry.name}/status", encoding="ascii") as file:
				rss = next(int(line.split()[1]) * 1024 for line in file if line.startswith("VmRSS:"))
			result.append({
				"pid": int(entry.name),
				"name": fields[1].strip("()")[:24],
				"state": fields[2],
				"rss": rss,
			})
		except (FileNotFoundError, PermissionError, StopIteration, ValueError):
			continue
	return sorted(result, key=lambda process: process["rss"], reverse=True)


def snapshot(previous_cpu, previous_net):
	current_cpu = cpu_times()
	current_net = network_bytes()
	disk = shutil.disk_usage("/")
	return {
		"cpu_percent": cpu_usage(previous_cpu, current_cpu),
		"memory": memory_info(),
		"disk": {"total": disk.total, "used": disk.used, "free": disk.free},
		"load": os.getloadavg(),
		"network": {
			"received_per_second": max(0, current_net[0] - previous_net[0]),
			"sent_per_second": max(0, current_net[1] - previous_net[1]),
		},
		"processes": processes(),
		"_cpu": current_cpu,
		"_net": current_net,
	}


def byte_size(value):
	amount = float(value)
	for unit in ("B", "K", "M", "G", "T"):
		if amount < 1024 or unit == "T":
			return f"{amount:6.1f}{unit}"
		amount /= 1024


def bar(width, percent):
	filled = max(0, min(width, int(width * percent / 100)))
	return "[" + "#" * filled + "." * (width - filled) + "]"


def draw(screen, data, interval):
	screen.erase()
	height, width = screen.getmaxyx()
	screen.addnstr(0, 0, " LINUX SYSTEM MONITOR ".center(width, "="), width - 1, curses.A_BOLD)
	memory = data["memory"]
	disk = data["disk"]
	memory_percent = 100 * memory["used"] / max(1, memory["total"])
	disk_percent = 100 * disk["used"] / max(1, disk["total"])
	bar_width = max(10, min(32, width - 48))
	lines = [
		f"CPU   {bar(bar_width, data['cpu_percent'])} {data['cpu_percent']:5.1f}%",
		f"MEM   {bar(bar_width, memory_percent)} {byte_size(memory['used'])} / {byte_size(memory['total'])}",
		f"DISK  {bar(bar_width, disk_percent)} {byte_size(disk['used'])} / {byte_size(disk['total'])}",
		f"LOAD  {data['load'][0]:.2f}  {data['load'][1]:.2f}  {data['load'][2]:.2f}    NET down {byte_size(data['network']['received_per_second'])}/s up {byte_size(data['network']['sent_per_second'])}/s",
	]
	for row, line in enumerate(lines, start=2):
		screen.addnstr(row, 2, line, width - 3)
	screen.addnstr(7, 2, "PID     STATE  RSS       COMMAND", width - 3, curses.A_BOLD)
	for row, process in enumerate(data["processes"][: max(0, height - 10)], start=8):
		line = f"{process['pid']:6}  {process['state']:^5}  {byte_size(process['rss']):>8}  {process['name']}"
		screen.addnstr(row, 2, line, width - 3)
	screen.addnstr(height - 1, 0, f"Refresh {interval:.1f}s | q quit | +/- adjust refresh".ljust(width), width - 1, curses.A_REVERSE)
	screen.refresh()


def monitor(screen, interval):
	curses.curs_set(0)
	screen.nodelay(True)
	previous_cpu = cpu_times()
	previous_net = network_bytes()
	last_update = 0.0
	data = None
	while True:
		key = screen.getch()
		if key in (ord("q"), ord("Q")):
			return
		if key in (ord("+"), ord("=")):
			interval = max(0.2, interval - 0.1)
		elif key in (ord("-"), ord("_")):
			interval = min(5.0, interval + 0.1)
		if data is None or time.monotonic() - last_update >= interval:
			data = snapshot(previous_cpu, previous_net)
			previous_cpu = data.pop("_cpu")
			previous_net = data.pop("_net")
			draw(screen, data, interval)
			last_update = time.monotonic()
		time.sleep(0.05)


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--once", action="store_true", help="print one JSON snapshot and exit")
	parser.add_argument("--interval", type=float, default=1.0, help="refresh interval in seconds")
	args = parser.parse_args()
	if args.once:
		previous_cpu = cpu_times()
		previous_net = network_bytes()
		time.sleep(0.1)
		data = snapshot(previous_cpu, previous_net)
		data.pop("_cpu")
		data.pop("_net")
		print(json.dumps(data, indent=2))
		return
	curses.wrapper(monitor, max(0.2, min(5.0, args.interval)))


if __name__ == "__main__":
	main()
