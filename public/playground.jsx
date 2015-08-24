/**
dashboard for presentation of test results in this case from jenkins
*/
var Col = ReactBootstrap.Col;

var TimerSinceUpdate = React.createClass({
    getInitialState: function() {
      return {elapsed: 0};
    },
    componentDidMount: function() {
      this.timer = setInterval(this.tick, 50);
    },
    componentWillUnmount: function() {
      clearInterval(this.timer);
    },
    tick: function() {
      this.setState({elapsed: new Date() - this.props.start});
    },
    render: function() {
      var elapsed = Math.round(this.state.elapsed / 100);
      var seconds = (elapsed / 10).toFixed(1);
      return <p>{seconds}</p>;
    }
});

var TimerBlock = React.createClass({
  render: function() {
    return (
      <Col className='dashi-card-size dashi-card-white dashi-card-size-mid'>
        <div className='dashi-card-text-timer'>
          <TimerSinceUpdate start={Date.now()} />
        </div>
      </Col>
    );
  }
});

var ResultBlock = React.createClass({
  render: function() {
    return (
      <Col className={this.props.colCss}>
        <div className='dashi-card-text'>
          <div>
            {this.props.name}
          </div>
          <div>
            pass: {this.props.pass}
          </div>
          <div>
            fail: {this.props.fail}
          </div>
          <div>
            build: {this.props.build}
          </div>
          <div>
            buildTime: {this.props.buildTime}
          </div>
          <div>
            buildResult: {this.props.buildResult}
          </div>
        </div>
      </Col>
    );
  }
});

var testStatus = function(pass, fail, buildResult) {
  classString = 'dashi-card-size dashi-card-size-mid'
  if (fail === 0 && pass >= 1) {
    return classString += ' dashi-card-pass';
  }
  else if (pass === 0) {
    return classString += ' dashi-card-fail'
  }
  else if (buildResult === 'ABORTED' || 'FAILURE') {
    return classString += ' dashi-card-grey';
  }
  else if (fail > 0) {
    return classString += ' dashi-card-warn';
  }
  else {
    return classString += ' dashi-card-grey';
  }
}

var ResultList = React.createClass({
    render: function() {
      var resultNodes = this.props.data.map(function (s) {
        var testResult = testStatus(s.pass, s.fail, s.result);
        return (
          <ResultBlock name={s.name} pass={s.pass} fail={s.fail} build={s.build} colCss={testResult} buildTime={s.buildDurationInSec} buildResult={s.result}/>
        );
      });
      const navInstance = (
        <div className='container-fluid'>
          {resultNodes}
          {resultNodes}
          <TimerBlock />
        </div>
      );
      return (
        navInstance
      );
    }
});

var ResultContainer = React.createClass({
  loadCommentsFromServer: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      cache: false,
      success: function(data) {
        this.setState({data: data});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: []};
  },
  componentDidMount: function() {
    this.loadCommentsFromServer();
    setInterval(this.loadCommentsFromServer, this.props.pollInterval);
  },
  render: function() {
    return (
      <div className="resultContainer">
        <ResultList data={this.state.data} />
      </div>
    );
  }
});

React.render(
  <ResultContainer url="/api/result" pollInterval={20000} />,
  document.getElementById('content')
);
