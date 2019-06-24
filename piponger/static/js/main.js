var last_gathered_data;

function prepare_label(label) {
    label = label.replace('_', ' ');
    var splitStr = label.toLowerCase().split(' ');
    for (var i = 0; i < splitStr.length; i++) {
        splitStr[i] = splitStr[i].charAt(0).toUpperCase() + splitStr[i].substring(1);
    }
    return splitStr.join(' ');
}

function toHHMMSS(date) {
    var sec_num = parseInt(date, 10); // don't forget the second param
    var hours = Math.floor(sec_num / 3600);
    var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
    var seconds = sec_num - (hours * 3600) - (minutes * 60);

    if (hours < 10) {
        hours = "0" + hours;
    }
    if (minutes < 10) {
        minutes = "0" + minutes;
    }
    if (seconds < 10) {
        seconds = "0" + seconds;
    }
    return hours + ':' + minutes + ':' + seconds;
}

function update_info() {

    $('#loading-ico').show();

    $.getJSON("/").done(function(data) {
        var items = [];

        last_gathered_data = data;

        if (data.hasOwnProperty('master_info')) {
            $("#master-table tbody").remove();
            var tbody = $('<tbody />', {}).appendTo("#master-table table");

            if (data.master_info.hasOwnProperty('current_iteration')) {
                $.each(data.master_info.current_iteration, function(key, val) {
                    var row = $('<tr />', {}).appendTo(tbody);

                    if (key == "progress") {
                        $('<td />', {
                            'text': prepare_label(key)
                        }).appendTo(row);
                        parsed_percent = parseInt(val.percentage, 10) + "%";
                        $('<td />', {
                            'text': val.percentage + "%"
                        }).appendTo(row);
                        $('#master-progress .progress-bar').attr('aria-valuenow', parsed_percent).css('width', parsed_percent);
                        $('#master-progress span').text(parsed_percent);
                        $('#master-progress').next('div').find('span').text(val.count + '/' + val.total);
                    } else if (key == "status") {
                        $('<td />', {
                            'text': prepare_label(key)
                        }).appendTo(row);
                        console.log(key, val);
                        if (val == "FINISHED") {
                            $('#start-btn').attr('disabled', false);
                            $('#start-btn').next('span').hide();
                        } else {
                            $('#start-btn').attr('disabled', true);
                            $('#start-btn').next('span').show().css('display', 'block');
                        }
                        $('<td />', {
                            'text': val
                        }).appendTo(row);
                    } else if (key == "created_date") {
                        $('<td />', {
                            'text': prepare_label(key)
                        }).appendTo(row);
                        $('<td />', {
                            'text': val
                        }).appendTo(row);

                        var unixTime = Date.parse(val);
                        var nowTime = Date.now();

                        var row = $('<tr />', {}).appendTo(tbody);
                        $('<td />', {
                            'text': "Time since creation"
                        }).appendTo(row);
                        $('<td />', {
                            'text': toHHMMSS((nowTime / 1000) - (unixTime / 1000))
                        }).appendTo(row);
                    } else if (key == "problematic_hosts") {
                        $("#master-prob-table tbody").remove();

                        if (val.length > 0) {
                            var tbody_prob = $('<tbody />', {}).appendTo("#master-prob-table table");
                            $.each(val, function(k, v) {
                                var row = $('<tr />', {}).appendTo(tbody_prob);
                                $('<td />', {
                                    'text': v.host
                                }).appendTo(row);
                                $('<td />', {
                                    'text': v.score
                                }).appendTo(row);
                            });
                        }
                    } else if (key == "has_graph") {
                        $('<td />', {
                            'text': prepare_label(key)
                        }).appendTo(row);
                        if (val == true) {
                            $('#load-img-btn').attr('disabled', false);
                            $('#load-img-btn').next('span').hide();

                            $('#load-net-js-btn').attr('disabled', false);
                            $('#load-net-js-btn').next('span').hide();
                        } else {
                            $('#load-img-btn').attr('disabled', true);
                            $('#load-img-btn').next('span').show().css('display', 'block');

                            $('#load-net-js-btn').attr('disabled', true);
                            $('#load-net-js-btn').next('span').show().css('display', 'block');
                        }
                        $('<td />', {
                            'text': val
                        }).appendTo(row);
                    } else {
                        $('<td />', {
                            'text': prepare_label(key)
                        }).appendTo(row);
                        $('<td />', {
                            'text': val
                        }).appendTo(row);
                    }
                });
            }

            $("#master-pinger-list-table tbody").remove();
            var tbody = $('<tbody />', {}).appendTo("#master-pinger-list-table table");
            $.each(data.master_info.registrered_pingers, function(key, val) {
                var row = $('<tr />', {}).appendTo(tbody);
                $('<td />', {
                    'text': val.address
                }).appendTo(row);
                $('<td />', {
                    'text': val.api_port
                }).appendTo(row);
                $('<td />', {
                    'text': val.api_protocol
                }).appendTo(row);
            });

            $("#master-ponger-list-table tbody").remove();
            var tbody = $('<tbody />', {}).appendTo("#master-ponger-list-table table");
            $.each(data.master_info.registrered_pongers, function(key, val) {
                var row = $('<tr />', {}).appendTo(tbody);
                $('<td />', {
                    'text': val.address
                }).appendTo(row);
                $('<td />', {
                    'text': val.api_port
                }).appendTo(row);
                $('<td />', {
                    'text': val.api_protocol
                }).appendTo(row);
            });
        }

        if (data.hasOwnProperty('pinger_info')) {
            var steps_hash_percent = {};
            steps_hash_percent['CREATED'] = 1;
            steps_hash_percent['RUNNING'] = 10;
            steps_hash_percent['RUNNING_TRACEROUTE'] = 40;
            steps_hash_percent['RUNNING_IPERF'] = 70;
            steps_hash_percent['RUNNING_FINISHING'] = 90;
            steps_hash_percent['FINISHED'] = 100;
            steps_hash_percent['ERROR'] = 100;

            var step_hash = {}
            step_hash['CREATED'] = 0;
            step_hash['RUNNING'] = 1;
            step_hash['RUNNING_TRACEROUTE'] = 2;
            step_hash['RUNNING_IPERF'] = 3;
            step_hash['RUNNING_FINISHING'] = 4;
            step_hash['FINISHED'] = 5;
            step_hash['ERROR'] = 5;

            $("#pinger-table tbody").remove();
            var tbody = $('<tbody />', {}).appendTo("#pinger-table table");
            $.each(data.pinger_info.last_iteration_status, function(key, val) {
                var row = $('<tr />', {}).appendTo(tbody);
                $('<td />', {
                    'text': prepare_label(key)
                }).appendTo(row);
                $('<td />', {
                    'text': val
                }).appendTo(row);

                if (key == "status") {
                    parsed_percent = steps_hash_percent[val] + "%";
                    step = step_hash[val];
                    $('#pinger-progress .progress-bar').attr('aria-valuenow', parsed_percent).css('width', parsed_percent);
                    $('#pinger-progress span').text(parsed_percent);
                    $('#pinger-progress').next('div').find('span').text(step + '/5');
                }
            });

            $("#ponger-list-table tbody").remove();
            var tbody = $('<tbody />', {}).appendTo("#ponger-list-table table");
            console.log(data.pinger_info.ponger_list);
            $.each(data.pinger_info.ponger_list, function(key, val) {
                var row = $('<tr />', {}).appendTo(tbody);
                console.log(val);
                $('<td />', {
                    'text': val.address
                }).appendTo(row);
                $('<td />', {
                    'text': val.api_port
                }).appendTo(row);
                $('<td />', {
                    'text': val.api_protocol
                }).appendTo(row);
            });


        }

    }).always(function(data) {
        window.setTimeout(function() {
            $('#loading-ico').hide();
        }, 500);
    });
}

$(document).ready(function() {
    $("#year").html((new Date()).getFullYear());

    window.setInterval(function() {
        update_info();
    }, 2500);

    $('#start-btn').on('click', function() {
        if ($(this).attr('disabled')) {
            return false;
        } else {
            $.getJSON("/force_create_iteration").
            done(function(data) {
                    if (data.result == "success") {
                        $('#start-btn').attr('disabled', true);
                    } else {
                        bootbox.alert({
                            size: "small",
                            title: "Error",
                            message: data.msg
                        })
                    }
                })
                .fail(function(data) {
                    bootbox.alert({
                        size: "small",
                        title: "Error",
                        message: "There was an error performing this request, please try again later"
                    })
                });
        }

        return false;
    });

    $('#load-img-btn').on('click', function() {
        if ($(this).attr('disabled')) {
            return false;
        } else {
            if (last_gathered_data && last_gathered_data.hasOwnProperty('master_info')) {
                $.each(last_gathered_data.master_info.current_iteration, function(key, val) {
                    if (key == "id") {
                        window.open("/get_result_plot/" + val, '_blank');
                        return true;
                    }
                });
            }
        }

        return false;
    });


    $('#load-net-js-btn').on('click', function() {
        if ($(this).attr('disabled')) {
            return false;
        } else {
            if (last_gathered_data && last_gathered_data.hasOwnProperty('master_info')) {
                $.each(last_gathered_data.master_info.current_iteration, function(key, val) {
                    if (key == "id") {
                        window.open("/get_result_plot_js/" + val, '_blank');
                        return true;
                    }
                });
            }
        }

        return false;
    });

    update_info();
});