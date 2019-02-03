import React, {Component} from 'react';

import './ScanBarcode.scss';

export default class ScanBarcode extends Component {
    constructor(props) {
        super(props);

        this.scanDisp = React.createRef();
    }

    componentDidMount() {
       this.socket = new WebSocket("ws://localhost:9090/ws");
       this.socket.onopen = this.socketOpen.bind(this);
       this.socket.onmessage = this.socketMessage.bind(this);
    }

    socketOpen() {
        this.socket.send(JSON.stringify({
            type: 0,
            data: {
                cmd: 0,
                data: null
            }
        }));
    }

    socketMessage(msg) {
        let data = null
        try {
            data = JSON.parse(msg.data);
        } catch(e) {
            if (e instanceof SyntaxError) {
                this.socket.close();
                return;
            }
        }
        if (!(data.hasOwnProperty('type') && data.hasOwnProperty('data'))) {
            this.socket.close();
            return;
        }
        if (data.type === 1) {
            this.handleBarcodeData(data.data);
        }
    }

    handleBarcodeData(data) {
        if (!(data.hasOwnProperty('img') && data.hasOwnProperty('codes'))) {
            this.socket.close();
            return;
        }
        const canvas = this.scanDisp.current;
        const ctx = canvas.getContext("2d");
        const img = new Image();
        img.src = "data:image/gif;base64," + data.img;
        img.onload = () => {
            const imgWidth = img.naturalWidth;
            const imgHeight = img.naturalHeight;
            const canvasWidth = canvas.offsetWidth;
            const canvasHeight = canvas.offsetHeight;
            canvas.width = canvasWidth;
            canvas.height = canvasHeight;
            let scaleX = 1;
            if (imgWidth > canvasWidth) {
                scaleX = canvasWidth/imgWidth;
            }
            let scaleY = 1;
            if (imgHeight > canvasHeight) {
                scaleY = canvasHeight/imgHeight;
            }
            let scale = scaleY;
            if (scaleX < scaleY) {
                scale = scaleX;
            }
            console.log(imgWidth, imgHeight, canvasWidth, canvasHeight, scaleX, scaleY, scale, imgWidth*scale, imgHeight*scale);

            ctx.drawImage(img, 0, 0,imgWidth*scale, imgHeight*scale);
        }
    }

    render() {
        return <div id="ScanBarcode">
            <canvas ref={this.scanDisp}/>
            <div>

            </div>
        </div>;
    }
}