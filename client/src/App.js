import React, { Component } from 'react';
import logo from './logo.svg';
import BarChart from './BarChart'
import './App.css';

class App extends Component {
  state = {
    data: {}
  }

  componentDidMount() {
    const url = window.location
    this.socket = new WebSocket('ws://' + url.hostname + ':8080' + '/socket');
    this.socket.onmessage = (msg) => {
      var data = JSON.parse(msg.data)
      this.setState({data: data.value})
    };
  }

  componentWillUnmount() {
    this.socket.close();
  }

  render() {
    return (
      <div style={{display:'flex', width: '100%'}}>
        {
          Object.keys(this.state.data).map((key) => {
            const bids = this.state.data[key]['bid']
            return (
              <div className="col" {...{key}}>
                <div className="col">
                  <div>
                    <BarChart data={Object.keys(bids).map((key) => Number(bids[key]))} size={[500,500]} />
                  </div>
                  <div style={{display:'flex', width: '100%'}}>
                      <pre>
                      {`POLO: ${key}`}
                      </pre>
                    </div>
                    <div style={{display:'flex', width: '100%'}}>
                      <pre>
                        {JSON.stringify(this.state.data[key].vwap, null, '  ')}
                      </pre>
                    </div>
                    <div style={{display:'flex', width: '100%'}}>
                      <pre>
                        {JSON.stringify(this.state.data[key].trade, null, '  ')}
                      </pre>
                    </div>
                    <div style={{display:'flex', width: '100%'}}>
                      <div className="col">
                        <pre>
                          {'bids'}
                          {JSON.stringify(this.state.data[key]['bid'], null, '  ')}
                        </pre>
                      </div>
                      <div className="col">
                        <pre>
                        {'asks'}
                          {JSON.stringify(this.state.data[key]['ask'], null, '  ')}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
            )
          })
        }
      </div>
    );
  }
}

export default App;
