import React, {Component} from 'react';
import {SocketContext} from '../App';
import "./SortProduct.scss"

class SortProduct extends Component {
    constructor(props) {
        super(props);

        this.state = {
            curPart: 0,
        };

        this.nextPart = this.nextPart.bind(this);
        this.prevPart = this.prevPart.bind(this);
        this.complete = this.complete.bind(this);
    }

    componentDidMount() {
        this.props.socket.sendMessage(0, {
            cmd: 4,
            data: null
        });

        const curPart = this.props.product.productpartSet.edges[this.state.curPart].node;
        this.props.socket.sendMessage(0, {
            cmd: 2,
            data: curPart.material.bin.id
        });
    }

    nextPart() {
        const curPart = this.props.product.productpartSet.edges[this.state.curPart].node;
        const nextId = this.state.curPart + 1;
        const nextPart = this.props.product.productpartSet.edges[nextId].node;

        this.props.socket.sendMessage(0, {
            cmd: 3,
            data: curPart.material.bin.id
        });
        this.props.socket.sendMessage(0, {
            cmd: 2,
            data: nextPart.material.bin.id
        });

        this.setState({
            curPart: nextId
        });
    }

    prevPart() {
        const curPart = this.props.product.productpartSet.edges[this.state.curPart].node;
        const prevId = this.state.curPart - 1;
        const prevPart = this.props.product.productpartSet.edges[prevId].node;

        this.props.socket.sendMessage(0, {
            cmd: 3,
            data: curPart.material.bin.id
        });
        this.props.socket.sendMessage(0, {
            cmd: 2,
            data: prevPart.material.bin.id
        });

        this.setState({
            curPart: prevId
        })
    }

    complete() {
        this.props.socket.sendMessage(0, {
            cmd: 4,
            data: null
        });
        this.props.onBack();
    }

    render() {
        const numParts = this.props.product.productpartSet.edges.length;
        const isNext = this.state.curPart < numParts - 1;
        const isPrevious = this.state.curPart > 0;
        const curPart = this.props.product.productpartSet.edges[this.state.curPart].node;

        return <div id="SortProduct">
            <div className="top">
                <img src="/material-design-icons/navigation/svg/production/ic_arrow_back_48px.svg" alt=""
                     onClick={this.props.onBack}/>
            </div>
            <div>
                <h2>Sorting {this.props.product.brand.name} {this.props.product.name}</h2>
                <h1>Place the {curPart.name} in the {curPart.material.bin.name}</h1>
            </div>
            <div className="buttons">
                {isPrevious ?
                    <button onClick={this.prevPart}>Previous</button>
                    : <div/>}
                {isNext ? <button onClick={this.nextPart}>Next</button>
                    : <button onClick={this.complete}>Done</button>}
            </div>
        </div>;
    }
}

export default React.forwardRef((props, ref) => (
    <SocketContext.Consumer>
        {value => <SortProduct socket={value} ref={ref} {...props}/>}
    </SocketContext.Consumer>
))