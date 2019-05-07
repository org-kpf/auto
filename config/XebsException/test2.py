import wmi
c = wmi.WMI ()
filename = r"D:\4K-4M-20Bucket.txt"
process = c.Win32_Process
process_id, result = process.Create (CommandLine="notepad.exe" + filename)
watcher = c.watch_for (
notification_type="Deletion",
wmi_class="Win32_Process",
delay_secs=1,
ProcessId=process_id
)
watcher ()
print "This is what you wrote:"
print open(filename).read()
