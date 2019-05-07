*** Settings ***
Library           EBS.py
Resource          client.txt
Resource          cluster.txt
Library           linux_client.py
Resource          client_nas.txt

*** Test Cases ***
XScaler-1488 服务器短时间掉电-文件网关角色
    [Template]
    [Timeout]
    cifs_mount
    create_vdbench_param_file
    put_vdbench_param_file
    start_vdbench_file
    sleep    60
    vdbench_check
    cluster_status_check    @{admin_ip}
    ${clusterIpList}    Evaluate    ' '.join(@{admin_ip})
    log    ${clusterIpList}
    ${pingIp}    EBS.Ping    ${clusterIpList}
    log    ${pingIp}
    ${rolse_result}    ebs_connect    ${pingIp}    ${server_user}    ${server_password}    ${admin_user}    ${user_password}
    Log Many    ${rolse_result}
    ${vip_result}    ebs.vip    ${pingIp}    ${server_user}    ${server_password}    ${admin_user}    ${user_password}
    Log many    ${vip_result}
    ${fgwips}    get_file_gateway    ${pingIp}    ${server_user}    ${server_password}    ${admin_user}    ${user_password}
    Comment    Log many    ${fgwips}
    : FOR    ${ip}    IN    ${fgwips}
    \    Comment    log    ${ip}
    \    ${ip}    Evaluate    random.choice(@{fgwips})    random
    \    log    ${ip}
    ${bmcip}    EBS.trans_ip    ${ip}    ${bmc_net}
    log    ${bmcip}
    ${power_fgw}    power_filegw    ${bmcip}    ${bmc_user}    ${bmc_password}    ${sleepTime_S}
    log    ${power_fgw}
    sleep    60
    vdbench_check

Test
    [Timeout]
    cluster_status_check    @{admin_ip}

*** Keywords ***
vdbench_check
    linux_client_connect    @{client_ip}[0]    ${client_user}    ${client_password}
    Comment    log    ${result}
    Comment    ${res}    linux_client.Cmd    df -h
    Comment    log    ${res}
    ${vdbench_check_result}    linux_client.Get Vdbench Result    ${path}
    Comment    log    ${vdbench_check_result}

connect_win_client
    ${res}    win_client_connect    ${win_ip}    ${win_user}    ${win_password}
    log    ${res]

connect_cluster_status-bak
    [Arguments]    @{admin_ip}
    ${L}    Evaluate    ' '.join(@{admin_ip})
    log    ${L}
    ${res}    EBS.Ping    ${L}
    log    ${res}
    ${status}    EBS.Check Ceph Status    ${res}    ${server_user}    ${server_password}
    log    ${status}
    Run Keyword If    '${status}' \ == \ 'HEALTH_OK'    Exit For Loop
    log    outiside loop

cluster_status_check
    [Arguments]    @{admin_ip}
    : FOR    ${n}    IN RANGE    1    2881
    \    sleep    30
    \    log    "循环第"${n}"次"
    \    ${clusterIpList}    Evaluate    ' '.join(@{admin_ip})
    \    Comment    log    ${clusterIpList}
    \    ${pingIp}    EBS.Ping    ${clusterIpList}
    \    log    ${pingIp}
    \    ${cluster_status}    EBS.Check Ceph Status    ${pingIp}    ${server_user}    ${server_password}
    \    log    ${cluster_status}
    \    ${N}    EBS.timing    ${n}
    \    log    ${N}
    \    Run Keyword If    '${cluster_status}' \ == \ 'HEALTH_OK'    Exit For Loop
    log    outiside loop

create_vdbench_param
    ${vdbench_param}    linux_client.create_vdbench_param    @{client_ip}    ${client_user}    ${client_password}    ${vdbench_home}    ${threads}
    ...    ${size}    ${wd}    ${rd}
    log    ${vdbench_param}

put_vdbench_param
    ${res}    linux_client.put_vdbench_param    @{client_ip}    ${client_user}    ${client_password}    ${filename}
    log    ${res}

start_vdbench
    ${res}    linux_client.start_vdbench    @{client_ip}    ${client_user}    ${client_password}    ${vdbench_home}    ${filename}
    log    ${res}

cifs_mount
    ${res}    linux_client.cifs_mount    @{client_nas_ip}    ${client_nas_user}    ${client_nas_password}    ${cifs_share_address}    ${share_mount}
    ...    ${username}    ${password}    ${cifs_vers}
    log    ${res}

create_vdbench_param_file
    ${res}    linux_client.create_vdbench_param_file    @{client_nas_ip}    ${client_nas_user}    ${client_nas_password}    ${vdbench_home}    ${depth}
    ...    ${width}    ${files}    ${size}    ${fwd}    ${frd}
    log    ${res}

put_vdbench_param_file
    ${res}    linux_client.put_vdbench_param    @{client_ip}    ${client_user}    ${client_password}    ${filename_nas}
    log    ${res}

start_vdbench_file
    ${res}    linux_client.start_vdbench    @{client_ip}    ${client_user}    ${client_password}    ${vdbench_home}    ${filename_nas}
    log    ${res}

nfs_mount
    ${res}    linux_client.nfs_mount    @{client_nas_ip}    ${client_nas_user}    ${client_nas_password}    ${nfs_share_address}    ${share_mount}
    ...    ${vers}    ${mode}
    log    ${res}
