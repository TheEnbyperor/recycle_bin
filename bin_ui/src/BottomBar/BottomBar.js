import React, {Component} from 'react';

import "./BottomBar.scss";

export default class BottomBar extends Component {
    render() {
        return (
            <div id="BottomBar">
                <i className="material-icons md-48 wifi">&#xE1D8;</i>
                <span className="time">12:46 PM</span>
            </div>
        );
    }
}