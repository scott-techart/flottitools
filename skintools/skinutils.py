import pymel.core as pm


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