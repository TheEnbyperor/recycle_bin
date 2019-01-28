import React, { Component } from 'react';
import BottomBar from "./BottomBar/BottomBar";
import FrontPage from "./FrontPage/FrontPage";


class App extends Component {
  render() {
    return (
      <div id="App">
        <FrontPage/>
        <BottomBar/>
      </div>
    );
  }
}

export default App;
