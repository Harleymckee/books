var socket,
    url = window.location;

function connect() {
    socket = new WebSocket('ws://' + url.host + '/socket');

    socket.onmessage = function (msg) {
	      var data = JSON.parse(msg.data)
	      document.querySelector('#placeholder').innerHTML = JSON.stringify(data.value, null, '  ');
    };
}

window.onload = function () {
    connect();
};

window.onbeforeunload = function () {
    socket.close();
};