from contextlib import contextmanager


def get_skincluster(pynode):
    """Returns the pynode's connected skinCluster.
    Returns None if no skinCluster found.

    :param pynode: Any pynode that has a skinCluster connected to it.
    :return: nt.SkinCluster
    """
    skin = pynode.listHistory(type='skinCluster', future=False)
    try:
        return skin[0]
    except IndexError:
        return None


@contextmanager
def max_influences_normalize_weights_disabled(skin_cluster):
    """Disables normalize weights and maintain max influences
    attributes of a skin cluster on enter and re-enables them on exit.

    Some Maya commands like skinPercent can produce slightly unpredictable
    results when the skinCluster's normalize weights attribute is enabled.
    """
    influence_state = skin_cluster.maintainMaxInfluences.get()
    normalize_state = skin_cluster.setNormalizeWeights(q=True)
    skin_cluster.maintainMaxInfluences.set(False)
    skin_cluster.setNormalizeWeights(0)
    try:
        yield
    finally:
        skin_cluster.maintainMaxInfluences.set(influence_state)
        skin_cluster.setNormalizeWeights(normalize_state)