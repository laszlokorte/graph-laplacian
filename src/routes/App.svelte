<script>
	import {onMount} from 'svelte'
	import {eigs} from 'mathjs';
	import eigenpy from './eigen.py?raw'

	let computeEigen = $state(() => [])
 
	function onLoadjs() {
		return (node) => {
			node.onload= async () => {
				try {
					const pyodide = await loadPyodide();
			 		await pyodide.loadPackage("numpy");
					computeEigen = (matrix) => {
					
						pyodide.globals.set("L", matrix);
						pyodide.runPython(eigenpy); 

						const eigenvalues = pyodide.globals.get("vals_list").toJs();
						const eigenvectors = pyodide.globals.get("vecs_list").toJs();

						console.log(eigenvectors)

						return {
							eigenvalues: eigenvalues,
							eigenvectors: eigenvectors,
						}
					}
				} catch(e) {
					console.error(e)
				}
			}
		} 
	}
	
	const radius = 10
	const numf = new Intl.NumberFormat("en-US", { signDisplay: "always", maximumFractionDigits: 3, minimumFractionDigits: 3 });
	const magnumf = new Intl.NumberFormat("en-US", { signDisplay: "never", maximumFractionDigits: 3, minimumFractionDigits: 3 });
	const phasenumf = new Intl.NumberFormat("en-US", { signDisplay: "never", maximumFractionDigits: 3, minimumFractionDigits: 3 });
	const phaseSign = (x) => x<0?'-':'';
	let graph = $state({
		nodes: [{x:0,y:0}],
		edges: {},
	})

	function nodeDegree(n) {
		let count = 0;
		for(let m=0;m<graph.nodes.length;m++) {
			if(n!=m && hasEdge(n,m)) count++;
		}

		return count
	}

	function hasEdge(a,b) {
		if(a > b) {
			return hasEdge(b,a)
		} else if(a == b) {
			return true
		} else {
			return graph.edges[`${a}/${b}`] || false
		}
	}
	
	function setEdge(a,b, bool) {
		if(a>b) {
			setEdge(b,a,bool)
		} else if(a == b) {
			return 
		} else {
			graph.edges[`${a}/${b}`] = bool
		}
	}

	const D = $derived(graph.nodes.map((n,a) => Array(graph.nodes.length).fill(nodeDegree(a)).map((d,b) => a==b?d: 0)));

	const A = $derived(graph.nodes.map((n,a) => Array(graph.nodes.length).fill(nodeDegree(a)).map((d,b) => a==b?0: hasEdge(a,b) ? 1 : 0)));

	const L = $derived(graph.nodes.map((n,a) => Array(graph.nodes.length).fill(nodeDegree(a)).map((d,b) => a==b?d: hasEdge(a,b) ? -1:0)));
	
	const eig = $derived(computeEigen(L));

	$inspect(eig)
	
	function addNode(evt, pos) {
		graph.nodes.push(pos)
	}
	
	function withPosition(events) {
		return (node) => {
			const svg = node.tagName === "svg" ? node : node.ownerSVGElement;
			const pt = svg.createSVGPoint();

		  // transform to SVG coordinates
			
			function addPosition(fn) {
				return (evt) => {
				  pt.x = evt.clientX;
				  pt.y = evt.clientY;
					
				  const {x,y} = pt.matrixTransform( svg.getScreenCTM().inverse() );

					return fn(evt, {x,y})
				}
			}

			const handlers = Object.entries(events).map(([e,fn]) => [e, addPosition(fn)])
			
			handlers.forEach(([e,fn]) => {
				node.addEventListener(e, fn)
			})  
			return () => {
				handlers.forEach(([e,fn]) => {
					node.removeEventListener(e, fn)
				})
			}
		}
	}  
</script>

<title>Graph Spectral</title>

<svelte:head>
	<script src="https://cdn.jsdelivr.net/pyodide/v0.27.1/full/pyodide.js" {@attach onLoadjs()}></script>

</svelte:head>
<div class="stack">
<svg class="canvas stack-layer" viewBox="-500 -500 1000 1000" {@attach withPosition({click: addNode})}>
	{#each graph.nodes as node, a}
		<g>
			<circle cx={node.x} cy={node.y} r={2*radius} stroke="black" fill="white" />
			<circle cx={node.x} cy={node.y} r={radius} />
		</g>

		{#each graph.nodes as target, b}
			{#if b > a && hasEdge(a,b)}
				<line x1={node.x} y1={node.y} x2={target.x} y2={target.y} stroke="black" />
			{/if}
		{/each}
	{/each}
</svg>

	<div class="stack-layer corner">
	
		<details open>
			<summary>Edges</summary>

			<table>
				      	{#each L as l,a}
				         <tr>
				         	{#each l as v,b}
				            <td>
				            		<input 
				            		disabled={a==b} 
				            		 onchange={e => setEdge(a,b,e.currentTarget.checked)}
				            		type="checkbox" checked={hasEdge(a,b)} />
				            </td>
										{/each}
				         </tr>
								{/each}
				         
				      </table>
		</details>
	
		<details>
			<summary>Laplacian</summary>

			<math>
					<mrow>
				      <mo>[</mo>
				      <mtable>
				      	{#each D as r,a}
				         <mtr>
				         	{#each r as v,b}
				            <mtd>
				            	<mn>{v}</mn>
				            </mtd>
										{/each}
				         </mtr>
								{/each}
				         
				      </mtable>
				      <mo>]</mo>
				      <mo>-</mo>
				      <mo>[</mo>
				      <mtable>
				      	{#each A as r,a}
				         <mtr>
				         	{#each r as v,b}
				            <mtd>
				            	<mn>{v}</mn>
				            </mtd>
										{/each}
				         </mtr>
								{/each}
				         
				      </mtable>
				      <mo>]</mo>
				      <mo>=</mo>
<mo>[</mo>
				      <mtable>
				      	{#each L as r,a}
				         <mtr>
				         	{#each r as v,b}
				            <mtd>
				            	<mn>{v}</mn>
				            </mtd>
										{/each}
				         </mtr>
								{/each}
				         
				      </mtable>
				      <mo>]</mo>
				   </mrow>
				</math>
		</details>

		
		<details >
			<summary>EigenVectors</summary>
				<math>
					<mrow>
				      <mo>[</mo>
				      <mtable>
				      	{#each eig.eigenvectors as e}
				         <mtr>
				         	{#each e as {re,im,ang,mag}}
				            <mtd>
				            	<mn>{magnumf.format(mag)}</mn>
				            	<msup>
				            		<mn>e</mn>
				            		<mrow>
				            		 <mo>{phaseSign(ang)}</mo>
				            			<mn>j</mn>
				            		 <mo> 	&middot;</mo>
				            		<mn>{phasenumf.format(ang/2/Math.PI)}</mn>
				            		 <mo> 	&middot;</mo>
				            		<mn>2</mn>
				            		 <mo> 	&middot;</mo>
				            		<mn>&pi;</mn>
				            		</mrow>
				            	</msup>
				            </mtd>
										{/each}
				         </mtr>
								{/each}
				         
				      </mtable>
				      <mo>]</mo>
				   </mrow>
				</math>

				<math>
					<mrow>
				      <mo>[</mo>
				      <mtable>
				      	{#each eig.eigenvalues as {re,im,ang,mag}}
				         <mtr>
				            <mtd>
				            	<mn>{magnumf.format(mag)}</mn>
				            	<msup>
				            		<mn>e</mn>
				            		<mrow>
				            		 <mo>{phaseSign(ang)}</mo>
				            			<mn>j</mn>
				            		 <mo> 	&middot;</mo>
				            		<mn>{phasenumf.format(ang/2/Math.PI)}</mn>
				            		 <mo> 	&middot;</mo>
				            		<mn>2</mn>
				            		 <mo> 	&middot;</mo>
				            		<mn>&pi;</mn>
				            		</mrow>
				            	</msup>
				            </mtd>
				         </mtr>
								{/each}
				         
				      </mtable>
				      <mo>]</mo>
				   </mrow>
				</math>
		</details>

	</div>

</div>

<style>
	summary {
		cursor: pointer;
	}

	.stack {
		display: grid;
		grid-template-columns: 1fr;
		grid-template-rows: 1fr;
	}

	.stack-layer {
		grid-area: 1 / 1 / -1 / -1;
	}

	.canvas{
		display: block;
		width: 100%;
		height: 100%;
		align-self: stretch;
		justify-self: stretch;
	}

	.noclick {
		pointer-events: none;
	}
	
	.corner {
		align-self: start;
		justify-self: start;
	}

	.plain-list {
		list-style: none;
		padding: 0;
		margin: 0;
		font-family: monospace;
	}
</style>