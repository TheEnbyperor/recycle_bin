import React, {Component} from 'react';
import BottomBar from "./BottomBar/BottomBar";
import FrontPage from "./FrontPage/FrontPage";

export const SocketContext = React.createContext(null);

class App extends Component {
    state = {
        socketOpen: false
    };

    socketCallbacks = {};

    componentWillMount() {
        this.socket = new WebSocket("ws://localhost:9090/ws");
        this.socket.onopen = this.socketOpen.bind(this);
        this.socket.onclose = this.socketClose.bind(this);
        this.socket.onmessage = this.socketMessage.bind(this);
    }

    componentWillUnmount() {
        this.socket.close();
    }

    socketOpen() {
        this.setState({
            socketOpen: true
        });
    }

    socketClose() {
        console.warn("Socket closed, reopening");
        this.setState({
            socketOpen: false
        });
        this.socket = new WebSocket("ws://localhost:9090/ws");
        this.socket.onopen = this.socketOpen.bind(this);
        this.socket.onclose = this.socketClose.bind(this);
        this.socket.onmessage = this.socketMessage.bind(this);
    }

    sendMessage(type, data) {
        this.socket.send(JSON.stringify({
            type: type,
            data: data
        }));
    }

    socketMessage(msg) {
        let data = null;
        try {
            data = JSON.parse(msg.data);
        } catch (e) {
            if (e instanceof SyntaxError) {
                console.error("Invalid JSON syntax received from server");
                this.socket.close();
                return;
            } else {
                throw e;
            }
        }
        if (!(data.hasOwnProperty('type') && data.hasOwnProperty('data'))) {
            console.error("Invalid data structure received from server");
            this.socket.close();
            return;
        }
        if (typeof this.socketCallbacks[data.type] !== "undefined") {
            const len = this.socketCallbacks[data.type].length;
            for (let i = 0; i < len; i++) {
                this.socketCallbacks[data.type][i](data.data);
            }
        }
    }

    addSocketCallback(callback, msgType) {
        if (typeof this.socketCallbacks[msgType] === "undefined") {
            this.socketCallbacks[msgType] = []
        }
        if (this.socketCallbacks[msgType].indexOf(callback) < 0) {
            this.socketCallbacks[msgType].push(callback);
        }
    }

    removeSocketCallback(callback, msgType) {
        let index;
        if ((index = this.socketCallbacks[msgType].indexOf(callback)) >= 0) {
            this.socketCallbacks[msgType].splice(index, 1);
        }
    }

    render() {
        if (this.state.socketOpen) {
            return (
                <SocketContext.Provider value={{
                    sendMessage: this.sendMessage.bind(this),
                    addCallback: this.addSocketCallback.bind(this),
                    removeCallback: this.removeSocketCallback.bind(this),
                }}>
                    <div id="App">
                        <FrontPage/>
                        <BottomBar/>
                    </div>
                </SocketContext.Provider>
            );
        } else {
            return null;
        }
    }
}

export default App;
