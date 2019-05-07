import wmi

w = wmi.WMI()
for processor in w.Win32_Processor():
    print "Processor ID: %s" % processor.DeviceID
    print "Process Name: %s" % processor.Name.strip()
totalMemSize = 0
for memModule in w.Win32_PhysicalMemory():
    totalMemSize += int(memModule.Capacity)
print "Memory Capacity: %.2fMB" % (totalMemSize / 1048576)