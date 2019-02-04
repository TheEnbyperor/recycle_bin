import React, {Component} from 'react';
import moment from 'moment';

import "./BottomBar.scss";

export default class BottomBar extends Component {
    interval = null;
    state = {
      time: ""
    };

    componentDidMount() {
        this.interval = setInterval(this.updateTime.bind(this), 1000);
    }

    componentWillUnmount() {
        clearInterval(this.interval);
    }

    updateTime() {
        this.setState({
            time: moment().format("ddd Do MMM h:mm:ss A")
        })
    }

    render() {
        return (
            <div id="BottomBar">
                <img className="wifi" src="/material-design-icons/device/svg/production/ic_signal_wifi_3_bar_48px.svg" alt=""/>
                <span className="time">{this.state.time}</span>
            </div>
        );
    }
}