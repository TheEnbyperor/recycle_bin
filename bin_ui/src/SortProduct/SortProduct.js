import React, {Component} from 'react';
import {SocketContext} from '../App';
import "./SortProduct.scss"

class SortProduct extends Component {
    constructor(props) {
        super(props);

        this.state = {
            curPart: 0,
        }
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
                    <button onClick={() => this.setState({curPart: this.state.curPart - 1})}>Previous</button>
                    : <div/>}
                {isNext ? <button onClick={() => this.setState({curPart: this.state.curPart + 1})}>Next</button>
                    : <button onClick={this.props.onBack}>Done</button>}
            </div>
        </div>;
    }
}

export default React.forwardRef((props, ref) => (
    <SocketContext.Consumer>
        {value => <SortProduct socket={value} ref={ref} {...props}/>}
    </SocketContext.Consumer>
))