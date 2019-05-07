*** Settings ***
Library           linux_client.py
Library           Collections
Library           Screenshot
Library           EBS.py

*** Variables ***
@{admin_ip}       10.0.11.121    10.0.11.122    10.0.11.123
${server_user}    root
${server_password}    redhat
@{cluster_ip}     10.0.31.121    10.0.31.122    10.0.31.123
@{gateway_ip}     10.0.21.121    10.0.21.122    10.0.21.123
@{public_ip}      10.0.21.121    10.0.21.122    10.0.21.123
${admin_user}     admin
${admin_password}    admin
@{linux_client_1}    10.0.11.126    root    redhat
@{linux_client_1_business_ip}    10.0.11.126

*** Test Cases ***
case-2-9-2
    log many    @{admin_ip}
    local client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    Comment    Comment    ${result}    ebsconnect    @{admin_ip}[0]    ${server_user}    ${server_password}
    ${result}    ebsconnect    @{admin_ip}[1]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    log    @{admin_ip}[1]
    log    ${result.id}
    ${result}    EBS.cmd    df -h
    log    ${result}
    ${a}    Set Variable    /dev/sdf
    @{b}    Create List    ${a}
    Comment    @{lun_list}    Set Variable    ${a}
    log    ${a}
    log many    @{b}
    Comment    ${1}    ${2}    start_fio_io    @{b}

CreateList
    @{test}    create list    1    2    3
    log many    @{test}

ebs connect
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    log many    ${host1.id}    ${host1.name}    ${host1.type}    ${host1.rolse}    ${host1.public_ip}
    ${result1}    ebs.cmd    df -h
    log    ${result1}
    #登陆不同的节点，下发命令
    ${host2}    ebs connect    @{admin_ip}[1]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    log many    ${host2.id}    ${host2.name}
    ${result2}    ebs.cmd    df -h
    log    ${result2}

linux_client_connect
    linux_client_connect    @{linux_client_1}[0]    @{linux_client_1}[1]    @{linux_client_1}[2]
    ${result}    linux_client.cmd    df -h
    log    ${result}

ebs-cmd
    ${result1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${result2}    EBS.cmd    df -h
    log    ${result2}
    ${result3}    EBS.cmd    df -h /yumengde
    log    ${result3}

CreateHost
    log many    @{admin_ip}
    log    @{admin_ip}[0]
    log    @{admin_ip}[1]
    log    @{admin_ip}[2]
    Comment    ${host1}    Ebs Connect    @{admin_ip}[0]    ${server_user}    ${server_password}
    Comment    ${host1}    Ebs Connect    @{admin_ip}[1]    ${server_user}    ${server_password}
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    CreateHost    @{public_ip}[1]    @{cluster_ip}[1]    @{gateway_ip}[1]    @{admin_ip}[1]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    ${host3}    CreateHost    @{public_ip}[2]    @{cluster_ip}[2]    @{gateway_ip}[2]    @{admin_ip}[2]    block_storage_gateway
    ...    storage_server    check_times=${1000}    check_interval=${3}
    log    ${host1.id}

ShowHost
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    ShowHost    @{admin_ip}[1]
    ${host3}    ShowHost    @{admin_ip}[2]
    log many    ${host1}
    log many    ${host1.id}    ${host2.id}    ${host3.id}
    @{host_list}    Create List    ${host1}    ${host2}    ${host3}
    log many    @{host_list}
    ${length1}    Get Length    ${host_list}
    log    ${length1}

GetAllDisk
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{disk_list1}    GetAllDisk    HDD
    log many    @{disk_list1}
    log    ${disk_list1}

GetDisk
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    ShowHost    @{admin_ip}[1]
    ${host3}    ShowHost    @{admin_ip}[2]
    @{host_list}    Create List    ${host1}    ${host3}    ${host2}
    log many    @{host_list}
    @{ssd_disk_list1}    GetDisk    ${host_list}    ${2}    SSD
    log many    ${ssd_disk_list1}
    @{hdd_disk_list1}    GetDisk    ${host_list}    ${4}    HDD
    log many    ${hdd_disk_list1}

CreatePartition
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    ShowHost    @{admin_ip}[1]
    ${hos31}    ShowHost    @{admin_ip}[2]
    @{host_list}    create list    ${host1}    ${host2}    ${hos31}
    log    ${host_list}
    @{ssd_disk_list}    GetDisk    ${host_list}    ${2}    SSD
    log many    @{ssd_disk_list}
    @{partition_list}    CreatePartition    ${ssd_disk_list}    ${3}    ${10}    ${3}
    #这个分区列表竟然是空的，不应该
    log    ${partition_list}
    @{hdd_disk_list}    GetDisk    ${host_list}    ${6}    HDD
    @{hybrid_osd_list}    CreateOsd    ${hdd_disk_list}    ${partition_list}    check_times=${100}    check_interval=${5}

DeletePartition
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    ShowHost    @{admin_ip}[1]
    ${hos31}    ShowHost    @{admin_ip}[2]
    @{host_list}    create list    ${host1}    ${host2}    ${hos31}
    log    ${host_list}
    @{ssd_disk_list}    GetDisk    ${host_list}    ${2}    SSD
    log    ${ssd_disk_list}
    @{partition_list}    CreatePartition    ${ssd_disk_list}    ${3}    check_times=${100}    check_interval=${5}
    ${result}    DeletePartition    ${ssd_disk_list}    check_times=${100}    check_interval=${5}

CreateOSD
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{disk_list1}    GetAllDisk    HDD
    log many    @{disk_list1}
    @{osd_list}    CreateOsd    ${disk_list1}

ShowOsd
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{hdd_osd_list1}    ShowOsd
    log many    @{hdd_osd_list1}
    log    ${hdd_osd_list1}

CreatePool
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{hdd_osd_list1}    ShowOsd
    ${result2}    CreatePool    ${hdd_osd_list1}    pool1    type=erasure    data_chunk_num=${2}    coding_chunk_num=${1}
    ...    check_times=${100}    check_interval=${5}
    log many    ${result2.id}    ${result2.type}    ${result2.name}    ${result2.pool_mode}

DeletePool
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${result}    DeletePool    pool1    check_times=${100}    check_interval=${3}
    log    ${result}
    Comment    should be empty    ${result}

Showpool
    ${result1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${pool1}    ShowPool    pool1
    log many    ${pool1.id}    ${pool1.type}    ${pool1.pool_mode}

CreateVolume
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${pool1}    ShowPool    pool1
    ${volume1}    CreateVolume    ${pool1.id}    100GB    volume2    check_times=${100}    check_interval=${5}
    log many    ${volume1.performance_priority}    ${volume1.id}    ${volume1.sn}
    ${volume1}    CreateVolume    ${pool1.id}    100GB    volume1    check_times=${100}    check_interval=${5}

ShowVolume
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${volume1}    ShowVolume    volume2
    log many    ${volume1.id}    ${volume1.name}    ${volume1.pool_id}    ${volume1.pool_name}
    @{test}    Create List    ${volume1.id}
    logmany    @{test}

SetVolume
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${volume1}    ShowVolume    volume1
    log many    ${volume1.size}    ${volume1.id}
    Comment    SetVolume    ${volume1.id}    check_times=${100}    check_interval=${3}    size=${10737418240}
    #修改失败，返回回显
    Comment    ${result}    SetVolume    ${volume1.id}    check_times=${100}    check_interval=${3}    size=${10737418240}
    Comment    log    ${result}
    #修改成功，没有返回
    ${result}    SetVolume    ${volume1.id}    check_times=${100}    check_interval=${3}    size=${10737418240}
    log    ${result}
    ${volume2}    ShowVolume    volume1
    log    ${volume2.size}

DeleteVolume
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${volume1}    ShowVolume    volume1
    ${result}    DeleteVolume    ${volume1.id}    ${100}    ${3}
    ${volume2}    ShowVolume    volume2
    ${result}    DeleteVolume    ${volume2.id}    ${100}    ${3}

CreateClientGroup
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    #check只接受int型的值
    Comment    ${cg-219}    CreateClientGroup    iSCSI    10.252.2.219    cg-219    1
    ...    ${10}    ${2}
    Comment    log many    ${cg-219.id}    ${cg-219.type}    ${cg-219.status}
    #变量名带-，调id属性居然报错
    ${cg2}    CreateClientGroup    iSCSI    10.252.2.218    cg218    1    ${10}
    ...    ${2}
    log many    ${cg2.id}    ${cg2.type}    ${cg2.status}

CreateAccessPath
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    Comment    ${ap1}    CreateAccessPath    iSCSI    ap1    123    abcABC123_321
    ...    false    1    ${10}    ${3}
    Comment    log many    ${ap1.id}    ${ap1.status}
    ${ap1}    CreateAccessPath    iSCSI    ap1    description=1    check_times=${10}    check_interval=${3}
    log many    ${ap1.id}    ${ap1.status}

ShowAccessPath
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${ap1}    ShowAccessPath    ap1
    log many    ${ap1.id}    ${ap1.status}

DeleteAccessPath
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${result}    DeleteAccesspath    ap2    check_times=${100}    check_interval=${3}

CreateTarget
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${ap1}    ShowAccessPath    ap1
    ${tg1}    CreateTarget    ${ap1.id}    ${host1.id}    ${10}    ${3}
    log    ${tg1.id}

ShowTarget
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{tg_ap_list1}    ShowTarget    ap1
    log many    @{tg_ap_list1}
    log    ${tg_ap_list1}
    ${target1}    set variable    @{tg_ap_list1}[0]
    #需要手动设置变量，才打印ID
    log    ${target1.id}

DeleteTarget
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${ap1}    ShowAccessPath    ap1
    ${result}    DeleteTarget    ap_id=${ap1.id}    host_id=${host1.id}    check_times=${100}    check_interval=${3}
    log    ${result}

CreateMappingGroup
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${lun1}    ShowVolume    volume1
    ${lun2}    ShowVolume    volume2
    @{lun_list}    Create List    ${lun1.id}    ${lun2.id}
    ${ap1}    ShowAccessPath    ap1
    ${cg1}    ShowClientGroup    cg218
    ${mg1}    CreateMappingGroup    ${lun_list}    ${ap1.id}    ${cg1.id}    ${100}    ${3}

ShowMappinggroup
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{result}    ShowMappinggroup    ap2
    logmany    @{result}
    log    @{result}[0]
    ${map1}    set variable    @{result}[0]
    log    ${map1.id}
    ${map2}    set variable    @{result}[1]
    log    ${map2.id}

DeleteMappinggroup
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    @{result}    ShowMappinggroup    ap1
    #为了取列表对象的ID
    ${map1}    set variable    @{result}[0]
    ${result}    DeleteMappinggroup    ${map1.id}    ${100}    ${3}

ShowClientGroup
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${cg1}    ShowClientGroup    cg218
    log    ${cg1.status}

ScanVolume
    local client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    #这2lun要提前映射给client
    ${volume1}    ShowVolume    volume1
    ${volume2}    ShowVolume    volume2
    #先构造LUN的SN组成的列表
    @{lun_sn}    create list    ${volume1.sn}    ${volume2.sn}
    log many    @{lun_sn}
    @{lun}    ScanVolume    ${lun_sn}
    log many    @{lun}
    log    ${lun}

MakeFilesystem
    local client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    Comment    ${lun}    set Variable    /dev/sdg
    MakeFilesystem    ext3    /dev/sdg

Mount
    local client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    #内容太多，放到用例去了
    ${result1}    mount    /dev/sdl    /mnt/test1
    should be equal    ${result1}    ${None}
    ${result2}    mount    /dev/sdm    /mnt/test2
    should be equal    ${result2}    ${None}

umount
    local client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    ${result1}    umount    /mnt/test1
    should be equal    ${result1}    ${None}
    ${result2}    umount    /mnt/test2
    should be equal    ${result2}    ${None}

StartFio
    local client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    @{file}    create list    /mnt/test1/file1
    log many    ${file}
    ${result}    StartFio    volume_list=${file}    rw=write    ioengine=libaio    thread=${null}    bs=1M
    ...    size=10GB    group_reporting=${null}    offset=${0}    iodepth=${32}
    log    ${result}

TEST-7640
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    CreateHost    @{public_ip}[1]    @{cluster_ip}[1]    @{gateway_ip}[1]    @{admin_ip}[1]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    ${host3}    CreateHost    @{public_ip}[2]    @{cluster_ip}[2]    @{gateway_ip}[2]    @{admin_ip}[2]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    Comment    ${host2}    ShowHost    @{admin_ip}[1]
    Comment    ${host3}    ShowHost    @{admin_ip}[2]
    @{host_list}    Create List    ${host1}    ${host3}    ${host2}
    #获取SSD,创建缓存分区
    @{ssd_disk_list}    GetDisk    ${host_list}    ${2}    SSD
    @{partition_list}    CreatePartition    ${ssd_disk_list}    ${3}    ${10}    ${3}
    #创建混合OSD
    @{hdd_disk_list}    GetDisk    ${host_list}    ${6}    HDD
    @{hybrid_osd_list}    CreateOsd    ${hdd_disk_list}    ${partition_list}    check_times=${100}    check_interval=${5}
    Comment    @{hybrid_osd_list}    ShowOsd
    #把创建OSD列表分成2份
    @{hybrid_osd_list_1}    SplitOsd    ${hybrid_osd_list}    ${2}    ${3}
    #创建EC池和副本池
    ${pool_ec}    CreatePool    @{hybrid_osd_list1}[0]    pool_ec    type=erasure    data_chunk_num=${2}    coding_chunk_num=${1}
    ...    check_times=${100}    check_interval=${5}
    ${pool_rep}    CreatePool    @{hybrid_osd_list1}[1]    pool_rep    check_times=${100}    check_interval=${5}
    #创建10GB的卷
    ${volume1}    CreateVolume    ${pool_ec.id}    10GB    volume1    check_times=${100}    check_interval=${5}
    ${volume2}    CreateVolume    ${pool_rep.id}    10GB    volume2    check_times=${100}    check_interval=${5}
    #卷扩容到50GB
    SetVolume    ${volume1.id}    check_times=${100}    check_interval=${3}    size=${53687091200}
    SetVolume    ${volume2.id}    check_times=${100}    check_interval=${3}    size=${53687091200}
    #把卷映射给local客户端
    ${ap1}    CreateAccessPath    Local    ap1    description=1    check_times=${10}    check_interval=${3}
    ${tg1}    CreateTarget    ${ap1.id}    ${host1.id}    ${10}    ${3}
    @{lun_list}    Create List    ${volume1.id}    ${volume2.id}
    ${mg1}    CreateMappingGroup    ${lun_list}    ${ap1.id}    check_times=${100}    check_interval=${3}
    #客户端扫卷
    linux client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    @{volume_sn}    create list    ${volume1.sn}    ${volume2.sn}
    @{disk_code}    ScanVolume    ${volume_sn}
    #客户端创建fs，并挂载
    ${result}    MakeFilesystem    ext3    @{disk_code}[0]
    should be equal    ${result}    ${None}
    ${result}    MakeFilesystem    ext3    @{disk_code}[1]
    should be equal    ${result}    ${None}
    ${result}    mount    @{disk_code}[0]    /mnt/test1
    should be equal    ${result}    ${None}
    ${result}    mount    @{disk_code}[1]    /mnt/test2
    should be equal    ${result}    ${None}
    #客户端写入20GB文件
    @{file1}    create list    /mnt/test1/file1    /mnt/test2/file1
    ${result}    StartFio    volume_list=${file1}    rw=write    ioengine=libaio    thread=${null}    bs=1M
    ...    size=20GB    group_reporting=${null}    offset=${0}    iodepth=${32}
    #客户端卸载目录
    ${result}    umount    /mnt/test1
    should be equal    ${result}    ${None}
    ${result}    umount    /mnt/test2
    should be equal    ${result}    ${None}
    #删除映射组
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${result}    DeleteMappinggroup    ${mg1.id}    ${100}    ${3}
    #卷缩容到20GB
    SetVolume    ${volume1.id}    check_times=${100}    check_interval=${3}    size=${21474836480}
    SetVolume    ${volume2.id}    check_times=${100}    check_interval=${3}    size=${21474836480}
    #重新创建映射组
    ${mg1}    CreateMappingGroup    ${lun_list}    ${ap1.id}    check_times=${100}    check_interval=${3}
    #客户端扫卷，创建fs，挂载，写30GB文件
    linux client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    @{volume_sn}    create list    ${volume1.sn}    ${volume2.sn}
    @{disk_code}    ScanVolume    ${volume_sn}
    ${result}    MakeFilesystem    ext3    @{disk_code}[0]
    should be equal    ${result}    ${None}
    ${result}    MakeFilesystem    ext3    @{disk_code}[1]
    should be equal    ${result}    ${None}
    ${result}    mount    @{disk_code}[0]    /mnt/test1
    should be equal    ${result}    ${None}
    ${result}    mount    @{disk_code}[1]    /mnt/test2
    should be equal    ${result}    ${None}
    @{file1}    create list    /mnt/test1/file1
    @{file2}    create list    /mnt/test2/file2
    ${result}    StartFio    volume_list=${file1}    rw=write    ioengine=libaio    thread=${null}    bs=1M
    ...    size=30GB    group_reporting=${null}    offset=${0}    iodepth=${32}
    should contain    ${result}    No space left on device
    ${result}    StartFio    volume_list=${file2}    rw=write    ioengine=libaio    thread=${null}    bs=1M
    ...    size=30GB    group_reporting=${null}    offset=${0}    iodepth=${32}
    should contain    ${result}    No space left on device
    #清理环境
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    Cleanup

TEST-7641
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    CreateHost    @{public_ip}[1]    @{cluster_ip}[1]    @{gateway_ip}[1]    @{admin_ip}[1]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    ${host3}    CreateHost    @{public_ip}[2]    @{cluster_ip}[2]    @{gateway_ip}[2]    @{admin_ip}[2]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    Comment    ${host2}    ShowHost    @{admin_ip}[1]
    Comment    ${host3}    ShowHost    @{admin_ip}[2]
    @{host_list}    Create List    ${host1}    ${host3}    ${host2}
    #获取SSD,创建缓存分区
    @{ssd_disk_list}    GetDisk    ${host_list}    ${2}    SSD
    @{partition_list}    CreatePartition    ${ssd_disk_list}    ${3}    ${10}    ${3}
    #创建混合OSD
    @{hdd_disk_list}    GetDisk    ${host_list}    ${6}    HDD
    @{hybrid_osd_list}    CreateOsd    ${hdd_disk_list}    ${partition_list}    check_times=${100}    check_interval=${5}
    Comment    @{hybrid_osd_list}    ShowOsd
    #把创建OSD列表分成2份
    @{hybrid_osd_list_1}    SplitOsd    ${hybrid_osd_list}    ${2}    ${3}
    #创建EC池和副本池
    ${pool_ec}    CreatePool    @{hybrid_osd_list1}[0]    pool_ec    type=erasure    data_chunk_num=${2}    coding_chunk_num=${1}
    ...    check_times=${100}    check_interval=${5}
    ${pool_rep}    CreatePool    @{hybrid_osd_list1}[1]    pool_rep    check_times=${100}    check_interval=${5}
    #创建卷
    ${volume1}    CreateVolume    ${pool_ec.id}    200GB    volume1    performance_priority=${1}    check_times=${100}
    ...    check_interval=${5}
    ${volume2}    CreateVolume    ${pool_rep.id}    200GB    volume2    check_times=${100}    check_interval=${5}
    #把卷映射给local客户端
    ${ap1}    CreateAccessPath    Local    ap1    description=1    check_times=${10}    check_interval=${3}
    ${tg1}    CreateTarget    ${ap1.id}    ${host1.id}    ${10}    ${3}
    @{lun_list}    Create List    ${volume1.id}    ${volume2.id}
    ${mg1}    CreateMappingGroup    ${lun_list}    ${ap1.id}    check_times=${100}    check_interval=${3}
    #客户端扫卷
    linux client connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${server_password}
    @{volume_sn}    create list    ${volume1.sn}    ${volume2.sn}
    @{disk_code}    ScanVolume    ${volume_sn}
    #客户端创建fs，并挂载
    ${result}    MakeFilesystem    ext4    @{disk_code}[0]
    should be equal    ${result}    ${None}
    ${result}    MakeFilesystem    xfs    @{disk_code}[1]
    should be equal    ${result}    ${None}
    ${result}    mount    @{disk_code}[0]    /mnt/test1
    should be equal    ${result}    ${None}
    ${result}    mount    @{disk_code}[1]    /mnt/test2
    should be equal    ${result}    ${None}
    #客户端对卷1写入100GB文件
    @{file1}    create list    /mnt/test1/file1
    ${result}    StartFio    volume_list=${file1}    rw=write    ioengine=libaio    thread=${null}    bs=1M
    ...    size=100GB    group_reporting=${null}    offset=${0}    iodepth=${32}
    #把卷1上的文件拷贝到卷2
    ${result}    ebs.cmd    cp /mnt/test1/file1 /mnt/test2/file1
    should be empty    ${result}
    #计算两个MD5并比较
    ${md5-file1}    ebs.cmd    md5sum /mnt/test1/file1 | awk '{print $1}'
    ${md5-file2}    ebs.cmd    md5sum /mnt/test2/file1 | awk '{print $1}'
    should be equal    ${md5-file1}    ${md5-file2}
    #卸载两个挂载目录，并删除文件
    ${result}    umount    /mnt/test1
    should be equal    ${result}    ${None}
    ${result}    umount    /mnt/test1
    should be equal    ${result}    ${None}
    #清理环境
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    Cleanup

TEST-6420
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${host2}    CreateHost    @{public_ip}[1]    @{cluster_ip}[1]    @{gateway_ip}[1]    @{admin_ip}[1]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    ${host3}    CreateHost    @{public_ip}[2]    @{cluster_ip}[2]    @{gateway_ip}[2]    @{admin_ip}[2]    block_storage_gateway
    ...    storage_server    1    ${1000}    ${5}
    @{host_list}    Create List    ${host1}    ${host3}    ${host2}
    #获取SSD,创建OSD
    @{ssd_disk_list}    GetDisk    ${host_list}    ${2}    SSD
    @{ssd_osd_list}    CreateOsd    ${ssd_disk_list}
    #创建2副本的SSD POOL
    ${pool1}    CreatePool    ${ssd_osd_list}    pool_ssd    check_times=${100}    check_interval=${3}
    #创建6个V3卷
    ${volume1}    CreateVolume    ${pool1.id}    100GB    volume1    check_times=${100}    check_interval=${3}
    ${volume2}    CreateVolume    ${pool1.id}    100GB    volume2    check_times=${100}    check_interval=${3}
    ${volume3}    CreateVolume    ${pool1.id}    100GB    volume3    check_times=${100}    check_interval=${3}
    ${volume4}    CreateVolume    ${pool1.id}    100GB    volume4    check_times=${100}    check_interval=${3}
    ${volume5}    CreateVolume    ${pool1.id}    100GB    volume5    check_times=${100}    check_interval=${3}
    ${volume6}    CreateVolume    ${pool1.id}    100GB    volume6    check_times=${100}    check_interval=${3}
    #映射2个卷给节点1
    ${ap1}    CreateAccessPath    Local    ap1    description=1    check_times=${10}    check_interval=${3}
    ${tg1}    CreateTarget    ${ap1.id}    ${host1.id}    ${10}    ${3}
    @{lun_list_1}    Create List    ${volume1.id}    ${volume2.id}
    ${mg1}    CreateMappingGroup    ${lun_list_1}    ${ap1.id}    check_times=${100}    check_interval=${3}
    #映射2个卷给节点2
    ${ap2}    CreateAccessPath    Local    ap2    description=1    check_times=${10}    check_interval=${3}
    ${tg2}    CreateTarget    ${ap2.id}    ${host2.id}    ${10}    ${3}
    @{lun_list_2}    Create List    ${volume3.id}    ${volume4.id}
    ${mg2}    CreateMappingGroup    ${lun_list_2}    ${ap2.id}    check_times=${100}    check_interval=${3}
    #映射2个卷给linux客户端FIO读写
    ${cg1}    CreateClientgroup    iSCSI    ${linux_client_1_business_ip}    cg1    check_times=${10}    check_interval=${3}
    ${ap3}    CreateAccessPath    iSCSI    ap3    description=1    check_times=${10}    check_interval=${3}
    ${tg3}    CreateTarget    ${ap3.id}    ${host3.id}    ${10}    ${3}
    @{lun_list_3}    Create List    ${volume5.id}    ${volume6.id}
    ${mg3}    CreateMappingGroup    ${lun_list_3}    ${ap3.id}    check_times=${100}    check_interval=${3}
    #local客户端1发现卷
    linux client connect    @{admin_ip}[0]    ${server_user}    ${server_password}
    @{volume_sn_1}    create list    ${volume1.sn}    ${volume2.sn}
    @{disk_code_1}    ScanVolume    ${volume_sn_1}
    should not be empty    @{disk_code}
    #local客户端2发现卷
    linux client connect    @{admin_ip}[1]    ${server_user}    ${server_password}
    @{volume_sn_2}    create list    ${volume3.sn}    ${volume4.sn}
    @{disk_code_2}    ScanVolume    ${volume_sn_2}
    should not be empty    @{disk_code_2}
    #linux客户端发现卷
    linux client connect    @{linux_client_1}[0]    @{linux_client_1}[1]    @{linux_client_1}[2]
    @{volume_sn_3}    create list    ${volume5.sn}    ${volume6.sn}
    @{disk_code_3}    ScanVolume    ${volume_sn_3}
    #无IO时，查看token的值
    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    ${result}    xdcadm    at    sys    show
    #无IO时，查看token borrow的值

test
    ${bianliang1}    set variable    space not enough
    ${bianliang2}    set variable    space not enough,and it
    should contain    ${bianliang2}    ${bianliang1}

Cleanup
    ${host1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    Cleanup

Test-1
    [Setup]
    循环
    @{list}    create list    a    c    d
    ${scalar}    create list    a    b
    ${ints}    create list    ${1}    ${2}
    ${dict1}    Create Dictionary    a=hello    b=world
    log    ${dict1}
    : FOR    ${value}    IN    @{list}
    \    log    ${value}
    \    run keyword if    '${value}'=='c'    log    '男孩'
    ${var}    Set Variable    hello
    Comment    Should Be Empty    ${var}
    Should Start With    ${var}    h    字符串以h开头
    Should Match    ${var}    hello
    Should Contain X Times    ${var}    hello    1
    ${args}    Set Variable    10
    Should Be Equal As Integers    ${args}    10
    ${strr}    Set Variable    hh
    Should Be Equal As Strings    ${strr}    hh
    ${num}    Set Variable    1.0
    Should Be Equal As Numbers    ${num}    1
    ${t}    get time
    log    ${t}
    Comment    sleep    3
    ${t}    get time
    ${nums}    Set Variable    79
    Run Keyword If    ${nums} >= 90    log    优秀
    ...    ELSE IF    ${nums}>=80    log    良好
    ...    ELSE IF    ${nums}>=70    log    一般
    ...    ELSE IF    ${nums}>=60    log    合格
    ...    ELSE    log    不及格
    : FOR    ${i}    IN RANGE    5
    \    log    ${i}
    ${j}    Evaluate    random.randint(1000,2340)    random
    log    ${j}
    Take Screenshot
    ${dict2}    Create Dictionary    k1    good    k2    very
    Comment    log    ${dict2}
    ${items}    Get Dictionary Items    ${dict2}
    log    ${items}
    ${k}    Get Dictionary Keys    ${dict2}
    log    ${k}
    ${v}    Get Dictionary Values    ${dict2}
    log    ${v}
    ${kv}    Get From Dictionary    ${dict2}    k1
    log    ${kv}

Test2
    循环

*** Keywords ***
laji
    [Arguments]    ${arg1}    ${arg2}

循环
    ${hosts1}    ebs connect    @{admin_ip}[0]    ${server_user}    ${server_password}    ${admin_user}    ${admin_password}
    log many    ${hosts1}
    Comment    log many    ${hosts1.id}    ${hosts1.name}
    Comment    ${result}    EBS.Cmd    df -h
    Comment    log    ${result}
