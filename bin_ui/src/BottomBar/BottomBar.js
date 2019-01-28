import React, {Component} from 'react';

import "./BottomBar.scss";

export default class BottomBar extends Component {
    render() {
        return (
            <div id="BottomBar">
                <img className="wifi" src="/material-design-icons/device/svg/production/ic_signal_wifi_3_bar_48px.svg" alt=""/>
                <span className="time">12:46 PM</span>
            </div>
        );
    }
}