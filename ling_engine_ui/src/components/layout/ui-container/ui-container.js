import React from 'react';
import Graph from 'react-graph-vis';
import {converter} from '../../../utils/transform-from-dfa-to-graph';
import clone from 'lodash/clone';

import './ui-container.scss';
import 'vis/dist/vis.css';
import TagsInput from 'react-tagsinput'

import 'react-tagsinput/react-tagsinput.css'

class UiContainer extends React.Component {
    constructor() {
        super();

        this.state = {
            alphabet: ["a", "b", "c"],
            states: [0, 1],
            initial: [0],
            finals: [1],
            transitionMap: '',
            graphInput: null
        };

        this._handleAlphabetChange = this._handleAlphabetChange.bind(this);
        this._handleStatesChange = this._handleStatesChange.bind(this);
        this._handleInitialChange = this._handleInitialChange.bind(this);
        this._handleFinalsChange = this._handleFinalsChange.bind(this);
        this._handleTransitionMapChange = this._handleTransitionMapChange.bind(this);
    }

    render() {
        let options = {
            layout: {
                randomSeed: undefined,
                improvedLayout: true,
                hierarchical: {
                    enabled: false,
                    levelSeparation: 150,
                    nodeSpacing: 100,
                    treeSpacing: 200,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true,
                    direction: 'UD',        // UD, DU, LR, RL
                    sortMethod: 'hubsize'   // hubsize, directed
                },
            },
            physics: {
                barnesHut: {
                    gravitationalConstant: 0.1,
                    centralGravity: 0.1, springConstant: 0
                }
            }
            // physics: {
            //     barnesHut: {
            //         gravitationalConstant: -2000,
            //         centralGravity: 0.3,
            //         springLength: 95,
            //         springConstant: 0.04,
            //         damping: 0.09,
            //         avoidOverlap: 1
            //     },
            // }
        };

        options = {
            edges: {
                smooth: {
                    type: 'cubicBezier',
                    roundness: 0.4
                }
            },
            layout: {
                improvedLayout: true,
                hierarchical: {
                    enabled: false,
                    levelSeparation: 150,
                    nodeSpacing: 100,
                    treeSpacing: 200,
                    blockShifting: true,
                    edgeMinimization: true,
                    parentCentralization: true,
                    direction: 'UD',        // UD, DU, LR, RL
                    sortMethod: 'hubsize'   // hubsize, directed
                },
            },
            physics:false
        };

        const events = {
            select: function (event) {
                const {nodes, edges} = event;
            }
        };

        const _renderMultipleInput = (_parentComponent, _stateKey, _onChange, _inputProps, _className = "react-tagsinput") => {
            return <TagsInput
                value={_parentComponent.state[_stateKey]}
                onChange={_onChange}
                inputProps={_inputProps}
                className={_className}
            />;
        };

        return (
            <div className="ui-container-wrapper container">
                <span className="alphabet-label mr-3">Input alphabet</span>
                {
                    _renderMultipleInput(this, 'alphabet', this._handleAlphabetChange, {placeholder: 'Add letter'})
                }

                <hr/>
                <span className="states-label mr-3">Input states</span>
                {
                    _renderMultipleInput(this, 'states', this._handleStatesChange, {placeholder: 'Add state'})
                }

                <hr/>
                <span className="initial-label mr-3">Input initial state</span>
                {
                    _renderMultipleInput(this, 'initial', this._handleInitialChange, {placeholder: 'Add initial'})
                }

                <hr/>
                <span className="finals-label mr-3">Input final states</span>
                {
                    _renderMultipleInput(this, 'finals', this._handleFinalsChange, {placeholder: 'Add final'})
                }

                <hr/>
                <span className="transition-map-label mr-3">Input transition map</span>
                <textarea value={this.state.transitionMap} onChange={this._handleTransitionMapChange}
                          className="json-area"/>

                <button
                    onClick={() => {
                        const generatedOut = this._generateGraphInput(this.state);

                        this.setState(
                            {
                                graphInput: generatedOut
                            }
                        );
                    }}>
                    Visualize!
                </button>

                {this.state.graphInput &&
                <Graph graph={converter(this.state.graphInput)} options={options} events={events}/>}
                {this.state.graphInput && console.log(converter(this.state.graphInput))}
            </div>
        );
    }

    _generateGraphInput(state) {
        return {
            alphabet: clone(state.alphabet),
            states: clone(state.states),
            initial: clone(state.initial)[0],
            finals: clone(state.finals),
            transitionMap: JSON.parse(state.transitionMap),
        }
    }

    _handleAlphabetChange(alphabet) {
        this.setState({alphabet})
    }

    _handleStatesChange(states) {
        this.setState({states})
    }

    _handleInitialChange(initial) {
        this.setState({initial})
    }

    _handleFinalsChange(finals) {
        this.setState({finals})
    }

    _handleTransitionMapChange(event) {
        this.setState({transitionMap: event.target.value})
    }
}

export default UiContainer;