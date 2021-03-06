import React from 'react';
import Graph from 'react-graph-vis';
import map from 'lodash/map';
import clone from 'lodash/clone';
import every from 'lodash/every';
import split from 'lodash/split';
import isEqual from 'lodash/isEqual';
import ReactDOM from 'react-dom';

import axios from 'axios';

import {converter} from '../../../../utils/transform-from-dfa-to-graph';
import {
    nfaGrammarTransitionMapExample,
    nfaTransitionMapFormat,
    visOptions
} from "../../../../constants/constants-values";

import TransitionMapInfoInModal from "../../stateless-helpers/transition-map-info-in-modal";
import 'vis/dist/vis.css';
import TagsInput from 'react-tagsinput'
import {JsonEditor as Editor} from 'jsoneditor-react';

import Modal from 'react-awesome-modal';

import ace from 'brace';
import 'brace/mode/json';
import 'brace/theme/github';

import {nfaToDfaApi, nfaToGrammarApi} from "../../../../config/api-endpoints";

import JSONPretty from 'react-json-pretty';

import '../../../../../node_modules/react-json-pretty/src/JSONPretty.monikai.css';

import 'jsoneditor-react/es/editor.min.css';
import 'react-tagsinput/react-tagsinput.css'
import './nfa-to-regular-grammar.scss';
import ReactLoading from 'react-loading';

class NfaToRegularGrammar extends React.Component {
    constructor() {
        super();

        this.state = {
            alphabet: ["a", "b"],
            states: ["Q", "W", "E"],
            initial: ["Q"],
            finals: ["W"],
            transitionMap: {},
            graphInput: null,
            isModalOpen: false,

            resultingAlphabet: null,
            resultingStates: null,
            resultingInitial: null,
            resultingFinals: null,
            resultingTransitionMap: null,

            resultingGrammar: null,

            loading: false,
        };

        this._handleAlphabetChange = this._handleAlphabetChange.bind(this);
        this._handleStatesChange = this._handleStatesChange.bind(this);
        this._handleInitialChange = this._handleInitialChange.bind(this);
        this._handleFinalsChange = this._handleFinalsChange.bind(this);
        this._handleTransitionMapChange = this._handleTransitionMapChange.bind(this);
        this._convertToRegularGrammar = this._convertToRegularGrammar.bind(this);
        this._closeModal = this._closeModal.bind(this);
        this._openModal = this._openModal.bind(this);

        this.isResultPresent = this.isResultPresent.bind(this);
    }

    isResultPresent() {
        const resultFields = [this.state.resultingGrammar];

        return every(resultFields, field => {
            return !isEqual(field, null);
        });
    }

    render() {
        this.state.graphInput && console.log(converter(this.state.graphInput));

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
            <div className="nfa-to-dfa container container">
                <h2>Nfa To Regular Grammar</h2>
                <Modal visible={this.state.isModalOpen} width="600" effect="fadeInUp"
                       onClickAway={() => this._closeModal()}>
                    <div className="container">
                        <TransitionMapInfoInModal
                            format={nfaTransitionMapFormat}
                            example={nfaGrammarTransitionMapExample}
                        />
                        <button className="btn btn-primary mb-4" onClick={() => this._closeModal()}>Close</button>
                    </div>
                </Modal>


                <div className="output-dfa-wrapper">
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
                </div>

                <hr/>
                <span className="transition-map-label d-inline-block mr-3 mb-3">Input transition map</span>

                <button type="button" className="btn btn-primary" onClick={this._openModal}>
                    View more information on transition map structure
                </button>

                <Editor
                    value={this.state.transitionMap}
                    onChange={this._handleTransitionMapChange}
                    ace={ace}
                    theme="ace/theme/github"
                    mode="code"
                />

                <button
                    className="btn btn-primary mt-3"
                    onClick={this._convertToRegularGrammar}>
                    Convert to Regular Grammar!
                </button>

                {
                    this.state.loading &&
                    <div className="spin-wrapper mt-4">
                        <ReactLoading height={30} width={30} color={"#000000"} type={"spin"}/>
                    </div>
                }

                <hr/>

                <h6>Resulting Regular Grammar</h6>

                {/*{"q0":["a","aq1"],"q1":["a","aq1"],"q2":["bq0"]}*/}

                {this.isResultPresent() && this.renderGrammar(this.state.resultingGrammar)}

                <hr/>

                <h6>Visualized DFA equivalent below:</h6>

                {this.state.graphInput &&
                <div className="graph-wrapper">
                    <Graph graph={converter(this.state.graphInput)} options={visOptions} events={events}/>
                </div>}
            </div>
        );
    }

    renderGrammar(resultingGrammar) {
        // {
        //   "q0": [
        //     "a",
        //     "aq1"
        // ],
        //   "q1": [
        //     "a",
        //     "aq1"
        // ],
        //   "q2": [
        //     "bq0"
        // ]
        // }

        console.log('renderin');
        return map(Object.entries(resultingGrammar), (grammarItems, value) => {
            const initial = grammarItems[0];
            let rules = clone(grammarItems);
            rules.shift();
            rules = split(rules, ',');

            return <div className={"grammar-section"}>{
                map(rules, (rule) => {
                    const display = `${initial} -> ${rule}`;
                    return <p>{display}</p>;
                })
            }</div>;
        });
    }

    _generateRequestBody(input) {
        return {
            alphabet: clone(input.alphabet),
            states: clone(input.states),
            initial: clone(input.initial)[0],
            finals: clone(input.finals),
            transitionMap: clone(input.transitionMap),
        }
    }

    _generateGraphInput(input) {
        return {
            alphabet: clone(input.resultingAlphabet),
            states: clone(input.resultingStates),
            initial: clone(input.resultingInitial),
            finals: clone(input.resultingFinals),
            transitionMap: clone(input.resultingTransitionMap),
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

    _handleTransitionMapChange(parsedMap) {
        this.setState({transitionMap: parsedMap})
    }

    _convertToRegularGrammar() {
        this.setState({
            loading: true,
        });

        const request = this._generateRequestBody(this.state);
        const component = this;

        axios.post(nfaToDfaApi, request).then(function (response) {
            const stateToSet = {
                resultingTransitionMap: response.data.transitionMap,
                resultingStates: response.data.states,
                resultingInitial: response.data.initial,
                resultingFinals: response.data.finals,
                resultingAlphabet: response.data.alphabet,
            };

            component.setState({
                ...stateToSet,
                graphInput: component._generateGraphInput(stateToSet),
                loading: false,
            });
        })
            .catch(function (error) {
                alert('Error while fetchin data!' + error);
            });

        axios.post(nfaToGrammarApi, request).then(function (response) {
            const stateToSet = {
                resultingGrammar: response.data.result,
            };

            component.setState({
                ...stateToSet,
                loading: false,
            });
        })
            .catch(function (error) {
                alert('Error while fetchin data!' + error);
            });
    }

    _closeModal() {
        this.setState({isModalOpen: false});
    }

    _openModal() {
        this.setState({isModalOpen: true});
    }
}

export default NfaToRegularGrammar;