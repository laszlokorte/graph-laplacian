<script>
	import {onMount} from 'svelte'
	import { on } from 'svelte/events';
	import {eigs} from 'mathjs';

	let computeEigen = $state(() => [])
 
	const radius = 10
	const numf = new Intl.NumberFormat("en-US", { signDisplay: "always", maximumFractionDigits: 3, minimumFractionDigits: 3 });
	const inputnumf = new Intl.NumberFormat("en-US", {maximumFractionDigits: 3, minimumFractionDigits: 3 });
	const phaseSign = (x) => x<0?'-':'';
	let graph = $state({
		nodes: Array(8).fill(0).map((_,i,all) => ({x:Math.cos(2*Math.PI*i/all.length)*200,y:Math.sin(2*Math.PI*i/all.length)*200, value:0, velo: 0})),
		edges: Object.fromEntries(Array(8).fill(0).map((_,i,all) => [[i%all.length,(i+1)%all.length].toSorted().join("/"), true])),
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

	function addNodeBetween(evt,a,b) {
		evt.stopPropagation()
		evt.preventDefault()
		setEdge(a,b,false)
		addNode(evt, {x: (graph.nodes[a].x + graph.nodes[b].x)/2,
			y: (graph.nodes[a].y + graph.nodes[b].y) / 2})

		setEdge(a,graph.nodes.length-1, true)
		setEdge(b,graph.nodes.length-1, true)

	}

	const D = $derived(graph.nodes.map((n,a) => Array(graph.nodes.length).fill(nodeDegree(a)).map((d,b) => a==b?d: 0)));

	const A = $derived(graph.nodes.map((n,a) => Array(graph.nodes.length).fill(nodeDegree(a)).map((d,b) => a==b?0: hasEdge(a,b) ? 1 : 0)));

	const L = $derived(graph.nodes.map((n,a) => Array(graph.nodes.length).fill(nodeDegree(a)).map((d,b) => a==b?d: hasEdge(a,b) ? -1:0)));
	
	const eig = $derived(L.length ? eigs(L): {eigenvectors: [], values: []});

	
	function addNode(evt, pos) {
		evt.stopPropagation()
		graph.nodes.push({...pos, value: 0, velo: 0})
	}

	function removeNode(i) {
		graph.nodes.splice(i, 1)
		graph.edges = Object.fromEntries(Object.entries(graph.edges).filter(([a,_]) => a.split("/").indexOf(""+i) < 0))
	}

	function draggable(node) {
		let dx = 0, dy = 0
		return withPosition({
			pointerdown: (evt, pos) => {
				if(evt.isPrimary) {
					evt.preventDefault()
					evt.currentTarget.setPointerCapture(evt.pointerId)
					dx = pos.x - node.x
					dy = pos.y - node.y
				}
			},
			pointermove: (evt, pos) => {
				if(evt.isPrimary && evt.currentTarget.hasPointerCapture(evt.pointerId)) {
					node.x = pos.x - dx
					node.y = pos.y - dy
				}

			},

			click: (evt) => {
				evt.stopPropagation()
			}

		})
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
			
			const dispose = handlers.map(([e,fn]) => on(node, e, fn))  
			return () => {
				dispose.forEach((d) => d())
			}
		}
	}  

	function loadEigen(index) {
		let i = 0;
		for(let v of eig.eigenvectors[index].vector) {
			graph.nodes[i].value = v
			graph.nodes[i].velo = 0
			i++
		}
	}

	let prevTime
	function iterate(time) {
		let dt = 200
		if(time && prevTime) {
			dt = time - prevTime
		} else if(prevTime) {
			prevTime = time
			raf = requestAnimationFrame(iterate)
			return
		}
		const newValues = Array(graph.nodes.length).fill(0)

		for(let i =0;i<newValues.length;i++) {
			for(let j =0;j<newValues.length;j++) {
				newValues[i] += L[i][j] * graph.nodes[j].value
			}
		}

		for(let i =0;i<newValues.length;i++) {
			graph.nodes[i].velo -= newValues[i] / 3
		}

		for(let i =0;i<newValues.length;i++) {
			graph.nodes[i].value  += graph.nodes[i].velo / 2000 * dt
		}

		if(playing && time) {
			prevTime = time
			raf = requestAnimationFrame(iterate)
		} else {

			prevTime = null
		}
	}

	let playing = $state(false)
	let raf = $state(null)

	function togglePlay() {
		playing = !playing
	}

	$effect(() => {
		if(playing) {
			raf = requestAnimationFrame(iterate)
		}

		return () => {
			prevTime = null
			cancelAnimationFrame(raf)
		}
	})
</script>

<title>Graph Spectral</title>

<div class="stack">
<svg class="canvas stack-layer" viewBox="-500 -500 1000 1000" {@attach withPosition({click: addNode})}>
	{#each graph.nodes as node, a}
		<g  {@attach draggable(node)}>
			<circle cx={node.x} cy={node.y} r={2*radius} stroke="black" fill="white" />
			<circle cx={node.x} cy={node.y} r={radius} />
			
<line stroke-linecap="round" x1={node.x} y1={node.y} y2={node.y} x2={node.x - node.velo*10} stroke={node.velo == 0 ? 'gray' : node.velo > 0 ? 'blue' : 'orange'} stroke-width="5" />
			<line stroke-linecap="round" x1={node.x} y1={node.y} x2={node.x} y2={node.y - node.value*100} stroke={node.value == 0 ? 'gray' : node.value > 0 ? 'green' : 'red'} stroke-width="5" />

			
		</g>

		{#each graph.nodes as target, b}
			{#if b > a && hasEdge(a,b)}
				<line x1={node.x} y1={node.y} x2={target.x} y2={target.y} stroke="black" />
				<circle cursor="pointer" onclick={e => addNodeBetween(e, a,b)} fill="#ffdd00aa" cx={(node.x + target.x)/2} cy={(node.y + target.y)/2} r={radius} />
			{/if}
		{/each}
	{/each}
</svg>

	<div class="stack-layer corner">
		<h2 class="titel">Graph Laplacian</h2>
		<details open>
			<summary>Edges</summary>

			<table>
				<thead>
		            <tr>
		            	<th>
		            	</th>
		            	<th>
		            	</th>
					{#each L as v,a}
				            <th>
				            		v{a}
				            </th>
					{/each}
				            <th>
				            	Value
				            </th>
				            <th>
				            	Momentum
				            </th>
		            </tr>
				</thead>
				      <tbody>
						{#each L as l,a}
				         <tr>
				            <th>
				            	<button onclick={e => removeNode(a)} type="button">x</button>
				            </th>
				            <th>
				            	v{a}
				            </th>
				         	{#each l as v,b}
				            <td>
				            		<input 
				            		disabled={a==b} 
				            		 onchange={e => setEdge(a,b,e.currentTarget.checked)}
				            		type="checkbox" checked={hasEdge(a,b)} />
				            </td>
										{/each}
				            <td>
				            	<input size="5" type="number" step="0.01" value={inputnumf.format(graph.nodes[a].value)} oninput={e => {
				            		graph.nodes[a].value = e.currentTarget.valueAsNumber
				            	}} />
				            </td>
				            <td>
				            	<input size="5" type="number" step="0.01" value={inputnumf.format(graph.nodes[a].velo)} oninput={e => {
				            		graph.nodes[a].velo = e.currentTarget.valueAsNumber
				            	}} />
				            </td>
				         </tr>
								{/each}
				      </tbody>
				         
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
		
		<button type="button" onclick={e => iterate()}>
		Iterate:
		<code>v := v - L * v</code>		

		</button>

		<button type="button" onclick={e => togglePlay()}>
		{!playing ? "Play" : "Pause"}	

		</button>

		
		<details >
			<summary>EigenVectors</summary>
				<math>
					<mrow>
				      <mo>[</mo>
				      <mtable>
				      	{#each eig.eigenvectors as e}
				         <mtr>
				         	{#each e.vector as v}
				            <mtd>
				            	<mn>{numf.format(v)}</mn>
				            	<!-- <msup>
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
				            	</msup> -->
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
				      	{#each eig.values as v, i}
				         <mtr>
				            <mtd>
				            	<mn>{numf.format(v)}</mn>
				            	<mn><button type="button" onclick={e => loadEigen(i)}>Load</button></mn>
				            	<!-- <msup>
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
				            	</msup> -->
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
		position: absolute;
		inset: 0;
		max-width: 100vw;
		max-height: 100vh;
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
	
	.titel {
		margin: 0;
	}

	.corner {
		align-self: start;
		justify-self: start;
		padding: 1em;
		background: #fffd;
		border: 2px solid #aaaa;
		margin: 1em;
		max-height: 90%;
		overflow: auto;
		max-width: 50%;
	}

	.plain-list {
		list-style: none;
		padding: 0;
		margin: 0;
		font-family: monospace;
	}
</style>