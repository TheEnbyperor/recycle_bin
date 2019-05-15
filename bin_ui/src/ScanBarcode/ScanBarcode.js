import React, {Component} from 'react';
import {SocketContext} from '../App';
import Loader from "../loader.svg";
import './ScanBarcode.scss';

class ScanBarcode extends Component {
    constructor(props) {
        super(props);

        this.scanDisp = React.createRef();
        this.handleBarcodeData = this.handleBarcodeData.bind(this);
        this.handleBarcodeCode = this.handleBarcodeCode.bind(this);
        this.handleLookupError = this.handleLookupError.bind(this);
        this.handleLookupSuccess = this.handleLookupSuccess.bind(this);
        this.scanAnother = this.scanAnother.bind(this);

        this.state = {
            currentStatus: "Looking for barcode...",
            currentError: null,
            barcodeData: null,
            product: null,
        }
    }

    componentDidMount() {
        this.props.socket.addCallback(this.handleBarcodeData, 1);
        this.props.socket.addCallback(this.handleBarcodeCode, 2);
        this.props.socket.addCallback(this.handleLookupError, 3);
        this.props.socket.addCallback(this.handleLookupSuccess, 4);
        this.props.socket.sendMessage(0, {
            cmd: 0,
            data: null
        });
    }

    componentWillUnmount() {
        this.props.socket.removeCallback(this.handleBarcodeData, 1);
        this.props.socket.removeCallback(this.handleBarcodeCode, 2);
        this.props.socket.removeCallback(this.handleLookupError, 3);
        this.props.socket.removeCallback(this.handleLookupSuccess, 4);
        this.props.socket.sendMessage(0, {
            cmd: 1,
            data: null
        });
    };


    handleBarcodeData(data) {
        const canvas = this.scanDisp.current;
        if (canvas !== null) {
            const ctx = canvas.getContext("2d");
            const img = new Image();
            img.src = "data:image/gif;base64," + data;
            img.onload = () => {
                const imgWidth = img.naturalWidth;
                const imgHeight = img.naturalHeight;
                const canvasWidth = canvas.offsetWidth;
                let scaleX = 1;
                if (imgWidth > canvasWidth) {
                    scaleX = canvasWidth / imgWidth;
                }
                let scaleY = 1;
                let scale = scaleY;
                if (scaleX < scaleY) {
                    scale = scaleX;
                }
                canvas.width = imgWidth * scale;
                canvas.height = imgHeight * scale;

                ctx.drawImage(img, 0, 0, imgWidth * scale, imgHeight * scale);
            }
        }
    }

    handleBarcodeCode(data) {
        this.props.socket.sendMessage(0, {
            cmd: 1,
            data: null
        });
        this.setState({
            currentStatus: "Looking up product...",
            currentError: null,
            barcodeData: data,
            product: null,
        })
    }

    handleLookupError(data) {
        this.props.socket.sendMessage(0, {
            cmd: 0,
            data: null
        });
        this.setState({
            currentStatus: "Looking for barcode...",
            currentError: data,
            product: null,
        })
    }

    handleLookupSuccess(data) {
        this.setState({
            currentStatus: "Found product!",
            currentError: null,
            product: data,
        })
    }

    scanAnother() {
        this.props.socket.sendMessage(0, {
            cmd: 0,
            data: null
        });
        this.setState({
            currentStatus: "Looking for barcode...",
            currentError: null,
            barcodeData: null,
            product: null,
        })
    }

    render() {
        return <div id="ScanBarcode">
            <div className="top">
                <img src="/material-design-icons/navigation/svg/production/ic_arrow_back_48px.svg" alt=""
                     onClick={this.props.onBack}/>
            </div>
            <canvas ref={this.scanDisp}/>
            <div>
                <h1>{this.state.currentStatus}</h1>
                <h3 className="error">{this.state.currentError}</h3>
                {(this.state.barcodeData === null) ? null : <h4>Barcode: {this.state.barcodeData}</h4>}
                {(this.state.product === null) ?
                    <object data={Loader} type="image/svg+xml">
                        Loading
                    </object>
                    :
                    <div className="product">
                        <h2>{this.state.product.brand.name} {this.state.product.name}</h2>
                        <button onClick={() => this.props.onScan(this.state.product)}>Continue</button>
                        <button onClick={this.scanAnother}>Scan another</button>
                    </div>
                }
            </div>
        </div>;
    }
}

export default React.forwardRef((props, ref) => (
    <SocketContext.Consumer>
        {value => <ScanBarcode socket={value} ref={ref} {...props}/>}
    </SocketContext.Consumer>
))