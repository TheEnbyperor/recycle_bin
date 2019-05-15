import React, {Component} from 'react';

import './FrontPage.scss';
import ScanBarcode from "../ScanBarcode/ScanBarcode";
import SortProduct from "../SortProduct/SortProduct";

export default class FrontPage extends Component {
    constructor(props) {
        super(props);

        this.state = {
            mode: 0,
            product: null,
        }
    }

    render() {
        if (this.state.mode === 0) {
            return <div id="FrontPage">
                <div onClick={() => this.setState({mode: 1})}>
                    <i className="fas fa-barcode"/>
                    <p>Scan barcode</p>
                </div>
                <div>
                    <i className="fas fa-search"/>
                    <p>Search manually</p>
                </div>
            </div>;
        } else if (this.state.mode === 1) {
            return <ScanBarcode onBack={() => this.setState({mode: 0})}
                                onScan={(product) => this.setState({mode: 2, product: product})}/>
        } else if (this.state.mode === 2) {
            return <SortProduct product={this.state.product} onBack={() => this.setState({mode: 0})}/>
        }
    }
}