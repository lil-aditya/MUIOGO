import { Base } from "../../Classes/Base.Class.js";
import { Html } from "../../Classes/Html.Class.js";
import { Message } from "../../Classes/Message.Class.js";
import { Osemosys } from "../../Classes/Osemosys.Class.js";

export default class ModelFile {

    static onLoad() {
        Html.renderTextStatus('#equations', 'Loading model equations...', 'info');
        Message.loaderStart('Loading model equations...');

        Promise.all([
            Base.getSession().catch(() => ({ session: null })),
            Osemosys.readModelFile()
        ])
            .then(([sessionResponse, modelText]) => {
                const casename = sessionResponse ? sessionResponse.session : null;
                Html.title(casename || 'No model selected', 'Model equations', '');

                const equations = ModelFile.extractEquations(modelText);
                if (equations.length === 0) {
                    Html.renderTextStatus('#equations', 'No model equations were detected in the current model file.', 'warning');
                    return;
                }

                ModelFile.renderEquations(equations);
            })
            .catch(error => {
                const message = error instanceof Error ? error.message : String(error);
                Html.renderTextStatus('#equations', message || 'Unable to load model equations.', 'danger');
            })
            .finally(() => {
                Message.loaderEnd();
            });
    }

    static extractEquations(text) {
        const source = (text || '').replace(/\r/g, '');
        const equations = [];

        const objectiveMatch = source.match(/(minimize|maximize)\s+([A-Za-z_]\w*)\s*:\s*([\s\S]*?)\s*;/i);
        if (objectiveMatch) {
            equations.push({
                section: 'Objective',
                name: objectiveMatch[2],
                latex: ModelFile.gmplToLatex(objectiveMatch[3].trim())
            });
        }

        const constraintPattern = /s\.t\.\s*([A-Za-z_]\w*)\s*(\{[^}]*\})?\s*:\s*([\s\S]*?);/gi;
        let match;
        while ((match = constraintPattern.exec(source)) !== null) {
            equations.push({
                section: ModelFile.detectSection(match[1]),
                name: match[1],
                latex: ModelFile.gmplToLatex(match[3].trim())
            });
        }

        return equations;
    }

    static detectSection(name) {
        const normalized = name.toUpperCase();

        if (normalized.startsWith('EB')) return 'Energy Balance';
        if (normalized.startsWith('E')) return 'Emissions';
        if (normalized.startsWith('A') || normalized.startsWith('TAC') || normalized.startsWith('AAC')) return 'Activity';
        if (normalized.startsWith('NC') || normalized.startsWith('TC') || normalized.startsWith('C')) return 'Capacity';
        if (normalized.startsWith('S')) return 'Storage';
        if (normalized.startsWith('UDC')) return 'User-defined Constraints';
        return 'Other';
    }

    static gmplToLatex(expression) {
        let output = expression;

        output = output.replace(/&&/g, ' \\land ');
        output = output.replace(/<=/g, '\\le ');
        output = output.replace(/>=/g, '\\ge ');
        output = output.replace(/\*/g, '\\cdot ');

        output = output.replace(/sum\s*\{([^}]*)\}/gi, (_, inside) => {
            const cleaned = inside
                .split(',')
                .map(part => part.trim().replace(/\s+in\s+/i, ' \\in '))
                .join(', ');
            return `\\sum_{${cleaned}}`;
        });

        output = output.replace(/([A-Za-z_]\w*)\s*\[([^\]]+)\]/g, '\\mathrm{$1}_{ $2 }');
        output = output.replace(/\n+/g, ' ');

        return output;
    }

    static renderEquations(equations) {
        const container = document.getElementById('equations');
        if (!container) {
            return;
        }

        container.textContent = '';

        let lastSection = '';
        let counter = 1;

        equations.forEach((equation, index) => {
            const isNewSection = equation.section !== lastSection;

            if (isNewSection && index !== 0) {
                const sectionSeparator = document.createElement('hr');
                sectionSeparator.className = 'section-sep';
                container.appendChild(sectionSeparator);
            }

            if (isNewSection) {
                const sectionHeading = document.createElement('h4');
                sectionHeading.className = 'mt-2 mb-3 model-section-heading';
                sectionHeading.textContent = equation.section;
                container.appendChild(sectionHeading);
                lastSection = equation.section;
            }

            const wrapper = document.createElement('div');
            wrapper.className = 'mb-3 model-equation';

            const name = document.createElement('div');
            name.className = 'text-secondary small mb-1';
            name.textContent = equation.name;
            wrapper.appendChild(name);

            const mathWrapper = document.createElement('div');
            mathWrapper.className = 'math-wrapper';
            mathWrapper.textContent = [
                '$$',
                '\\begin{align}',
                equation.latex,
                '\\end{align}',
                `\\tag{${counter}}`,
                '$$'
            ].join('\n');
            wrapper.appendChild(mathWrapper);

            const equationSeparator = document.createElement('hr');
            equationSeparator.className = 'eq-sep';
            wrapper.appendChild(equationSeparator);

            container.appendChild(wrapper);
            counter += 1;
        });

        ModelFile.typeset(container);
    }

    static typeset(container, retries = 40) {
        if (window.MathJax && typeof window.MathJax.typesetPromise === 'function') {
            if (typeof window.MathJax.typesetClear === 'function') {
                window.MathJax.typesetClear([container]);
            }

            window.MathJax.typesetPromise([container]).catch(error => {
                console.error('MathJax typeset failed:', error);
            });
            return;
        }

        if (retries <= 0) {
            return;
        }

        window.setTimeout(() => {
            ModelFile.typeset(container, retries - 1);
        }, 100);
    }
}
