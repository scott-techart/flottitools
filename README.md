# flottitools
A collection of Maya tools.

## Installation
Open a new scene in Maya and drag the named "drag_to_maya_scene_setup.py" into the Maya scene viewport.
A new shelf titled "FlottiTools" should appear in your Maya shelves bar.
![Alt](/docs/averageweights_install.gif "Install .gif")

## Usage
### Average Weights
This tool assists with polishing skin weighting quickly and cleanly.
![Alt](/docs/averageweights_demo_short.gif "Install .gif")
It will average the weight values of the user-selected sampled vertices and apply those values to the user-selected target vertices.
Average weights by Proximity will weight the average skin-weight values for each target vertex based on its distance in bind-bose in worldspace to the sampled vertices.

1. Launch the Average Weights tool by clicking the Average Weights button on the FlottiTools shelf.
2. Select one or more vertices of a skinned mesh in your Maya scene and click the "Sample Verts" button.
3. Select one or more other vertices and click either the "Average" or "Proximity" under the "Apply Skin Weights" section.
4. Check the weight values of the vertices in the component editor.

Common Use-cases:
1. Smoothing out edge loops.
> 1. Manually adjust the weights of at least two vertices on either end of an edge loop. 
> 2. Use Average Weights to sample the verts with "good" weights.
> 3. Use Proximity apply weights on the remaining vertices in the edge loop to quickly make a smooth weight distribution.
2. Quickly weight rigid elements on a skinned mesh.
> 1. Select one vertex that has the weight values you wish to copy and click "Sample Verts".
> 2. Select the vertices you wish to have identical weights and click "Average".
> (Applying the average of one vertex to multiple target vertices effectively copies the skin weight data of the sampled vertex to the target vertices.)

## License
[MIT](https://choosealicense.com/licenses/mit/)