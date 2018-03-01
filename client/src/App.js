import React, { Component } from 'react';
import logo from './logo.svg';
import {
  XYPlot,
  XAxis,
  YAxis,
  VerticalGridLines,
  HorizontalGridLines,
  VerticalBarSeries,
  VerticalBarSeriesCanvas
} from 'react-vis';
import './App.css';

const data = new Array(10).fill(0).reduce((prev, curr) => [...prev, {
  x: prev.slice(-1)[0].x + 1,
  y: prev.slice(-1)[0].y * (1 + Math.random() * 0.2)
}], [{ x: 0, y: 10 }])

// const Chart = () => (
//   <XYPlot
//     width={window.innerWidth - 50}
//     height={window.innerHeight - 50}>
//     <XAxis/>
//     <YAxis/>
//     <HorizontalGridLines />
//     <LineMarkSeries data={data} />
//   </XYPlot>
// )

class Example extends React.Component {
  state = {
    useCanvas: false
  }

  render() {
    const {useCanvas} = this.state;
    const content = useCanvas ? 'TOGGLE TO SVG' : 'TOGGLE TO CANVAS';
    const BarSeries = useCanvas ? VerticalBarSeriesCanvas : VerticalBarSeries;

    const transformed = Object.keys(this.props.data).map((key) => {
      return (
        {x: key, y: this.props.data[key]}
      )
      
    })
    return (
      <div>
        <XYPlot
          xType="ordinal"
          width={1200}
          height={1200}
          // xDistance={1000000}
          // Distance={1000000}
          >
          <VerticalGridLines />
          <HorizontalGridLines />
          <XAxis />
          <YAxis />
          <BarSeries
            className="vertical-bar-series-example"
            data={transformed}/>
          {/* <BarSeries
            data={[
              {x: 'A', y: 12},
              {x: 'B', y: 2},
              {x: 'C', y: 11}
            ]}/> */}
        </XYPlot>
      </div>
    );
  }
}

class App extends Component {
  state = {
    data: {
      // ETH_ZRX: {
        
      // },
      // ETH_OMG: {

      // }
    }
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
            return (
              <div className="col">
                <div className="col">
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
