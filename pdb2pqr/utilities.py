"""Utilities for PDB2PQR Suite

This module provides various utilities for the PDB2PQR suite to be imported
into other Python scripts.

Authors:  Todd Dolinsky, Yong Huang
"""
import math
import io
import logging
from collections import Counter
from pathlib import Path
from sys import path as sys_path
import numpy as np
import requests


SMALL = 1.0e-7
DIHEDRAL = 57.2958
FILTER_WARNINGS_LIMIT = 30
FILTER_WARNINGS = ["Skipped atom during water optimization",
                   "The best donorH was not picked"]
# TODO - list of forcefields should be somewhere else
TEST_FORCEFIELDS = ["amber", "charmm", "parse", "tyl06", "peoepb", "swanson"]


class DuplicateFilter(logging.Filter):
    """Filter duplicate messages."""
    def __init__(self):
        super().__init__()
        self.warn_count = Counter()

    def filter(self, record):
        """Filter current record."""
        if record.levelname == "WARNING":
            for fwarn in FILTER_WARNINGS:
                if record.getMessage().startswith(fwarn):
                    self.warn_count.update([fwarn])
                    if self.warn_count[fwarn] > FILTER_WARNINGS_LIMIT:
                        return False
                    elif self.warn_count[fwarn] == FILTER_WARNINGS_LIMIT:
                        _LOGGER.warning("Suppressing further '%s' messages", fwarn)
                        return False
                    else:
                        return True
        return True


_LOGGER = logging.getLogger(__name__)
_LOGGER.addFilter(DuplicateFilter())


class PROPKAoptions(object):
    """Namespace class for PROPKA options."""
    def __init__(self, ph, verbose=False, reference="neutral"):
        self.ph = ph
        self.reference = reference
        self.chains = None
        self.thermophiles = None
        self.alignment = None
        self.mutations = None
        self.verbose = verbose
        self.protonation = "old-school"
        self.window = (0.0, 14.0, 1.0)
        self.grid = (0.0, 14.0, 0.1)
        self.mutator = None
        self.mutator_options = None
        self.display_coupled_residues = None
        self.print_iterations = None
        self.version_label = "Nov30"


def sort_dict_by_value(inputdict):
    """Sort a dictionary by its values

    Args:
        inputdict:  The dictionary to sort (inputdict)
    Returns:
        items: The dictionary sorted by value (list)
    """
    items = [(v, k) for k, v in inputdict.items()]
    items.sort()
    items.reverse()
    items = [k for v, k in items]
    return items


def shortest_path(graph, start, end, path=[]):
    """Uses recursion to find the shortest path from one node to another in an
    unweighted graph.  Adapted from http://www.python.org/doc/essays/graphs.html

    Args:
        graph: A mapping of the graph to analyze, of the form
               {0: [1,2], 1:[3,4], ...} . Each key has a list of edges.
        start: The ID of the key to start the analysis from
        end:   The ID of the key to end the analysis
        path:  Optional argument used during the recursive step to keep the
        current path up to that point

    Returns:
        List of the shortest path (list) Returns None if start and end are not
        connected
    """
    path = path + [start]
    if start == end:
        return path
    if start not in graph:
        return None
    shortest = None
    for node in graph[start]:
        if node not in path:
            newpath = shortest_path(graph, node, end, path)
            if newpath:
                if not shortest or len(newpath) < len(shortest):
                    shortest = newpath
    return shortest


def analyze_connectivity(map_, key):
    """Analyze the connectivity of a given map using the key value.

    Args:
        map:  The map to analyze (dict)
        key:  The key value (variable)
    Returns:
        list: A list of connected values to the key (list)
    """
    clist = []
    keys = [key]
    while len(keys) > 0:
        key = keys[0]
        if key not in clist:
            clist.append(key)
            if key in map_:
                for value in map_[key]:
                    if value not in clist:
                        keys.append(value)
        keys.pop(keys.index(key))
    return clist


def test_for_file(name, type_):
    """Test for the existence of a file with a few name permutations.

    Args:
        name:  name of file
        type_:  type of file
    Returns:
        path to file or None
    """
    if name is None:
        return ''
    test_names = [name, name.upper(), name.lower()]
    test_suffixes = ["", ".%s" % type_.upper(), ".%s" % type_.lower()]

    test_dirs = sys_path + ["dat", "."]
    if name.lower() in TEST_FORCEFIELDS:
        name = name.upper()

    for test_dir in test_dirs:
        test_dir = Path(test_dir)
        for test_name in test_names:
            for test_suffix in test_suffixes:
                test_path = test_dir / (test_name + test_suffix)
                if test_path.is_file():
                    _LOGGER.debug("Found %s file %s", type_, test_path)
                    return test_path
    _LOGGER.warning("Unable to find %s file for %s", type_, name)
    return ""


def test_dat_file(name):
    """Test for the existence of the forcefield file with a few name permutations.

    Args:
        name of forcefield
    Returns:
        filename or empty string
    """
    return test_for_file(name, "DAT")


def test_names_file(name):
    """Test for the *.names file that contains the XML mapping.

    Args:
        name:  The name of the forcefield (string)
    Returns
        path:  The path to the file (string)
    """
    return test_for_file(name, "NAMES")


def get_pdb_file(name):
    """Obtain a PDB file.

    First check the path given on the command line - if that file is not
    available, obtain the file from the PDB webserver at http://www.rcsb.org/pdb/

    TODO - this should be a context manager (to close the open file)

    Args:
        name:  Name of PDB file to obtain (string)

    Returns
        file:  File object containing PDB file (file object)
    """
    path = Path(name)
    if path.is_file():
        return open(path, "rt", encoding="utf-8")
    else:
        url_path = "https://files.rcsb.org/download/" + path.stem + ".pdb"
        _LOGGER.debug("Attempting to fetch PDB from %s", url_path)
        resp = requests.get(url_path)
        if resp.status_code != 200:
            errstr = "Got code %d while retrieving %s" % (resp.status_code, url_path)
            raise IOError(errstr)
        return io.StringIO(resp.text)


# TODO - upgrade with numpy
def angle(coords1, coords2, coords3):
    """Get the angle between three coordinates

    Args:
        coords1:  The first coordinate set (atom)
        coords2:  The second (vertex) coordinate set (atom)
        coords3:  The third coordinate set (atom)
    Returns
        angle:  The angle between the atoms (float)
    """
    diff32 = np.array(coords3) - np.array(coords2)
    diff12 = np.array(coords1) - np.array(coords2)
    norm1 = normalize(diff32)
    norm2 = normalize(diff12)
    dotted = np.inner(norm1, norm2)
    if dotted > 1.0: # If normalized, this is due to rounding error
        dotted = 1.0
    rad = np.absolute(np.arccos(dotted))
    value = rad*180.0/np.pi
    if value > 180.0:
        value = 360.0 - value
    return value


def distance(coords1, coords2):
    """Calculate the distance between two coordinates, as denoted by

        dist = sqrt((x2- x1)^2 + (y2 - y1)^2 + (z2 - z1)^2))

    Args:
        coords1: Coordinates of form [x,y,z]
        coords2: Coordinates of form [x,y,z]
    Returns:
        dist:  Distance between the two coordinates (float)
    """
    coords1 = np.array(coords1)
    coords2 = np.array(coords2)
    return np.linalg.norm(coords1 - coords2)


# TODO - eliminate and replace with numpy in code
def add(coords1, coords2):
    """Add one 3-dimensional point to another

    Args:
        coords1: coordinates of form [x,y,z]
        coords2: coordinates of form [x,y,z]
    Returns
        list:  List of coordinates equal to coords2 + coords1 (list)
    """
    return np.array(coords1) + np.array(coords2)


# TODO - eliminate and replace with numpy in code
def subtract(coords1, coords2):
    """Subtract one 3-dimensional point from another

    Args:
        coords1: coordinates of form [x,y,z]
        coords2: coordinates of form [x,y,z]
    Returns
        list:  List of coordinates equal to coords1 - coords2 (list)
    """
    return np.array(coords1) - np.array(coords2)


# TODO - eliminate and replace with numpy in code
def cross(coords1, coords2):
    """Find the cross product of two 3-dimensional points

    Args:
        coords1: coordinates of form [x,y,z]
        coords2: coordinates of form [x,y,z]
    Returns
        list:  Cross product coords2 and coords1 (list)
    """
    return np.cross(np.array(coords1), np.array(coords2))


# TODO - eliminate and replace with numpy in code
def dot(coords1, coords2):
    """Find the dot product of two 3-dimensional points

    Args:
        coords1: coordinates of form [x,y,z]
        coords2: coordinates of form [x,y,z]
    Returns
        value:  Dot product coords2 and coords1 (float)
    """
    return np.inner(np.array(coords1), np.array(coords2))


# TODO - enhance with numpy
def normalize(coords):
    """Normalize a set of coordinates

    Args:
        coords: coordinates of form [x,y,z]
    Returns
        list: normalized coordinates (list)
    """
    return coords/np.linalg.norm(coords)


def factorial(num):
    """Returns the factorial of the given number n"""
    if num <= 1:
        return 1
    return num*factorial(num-1)


def dihedral(coords1, coords2, coords3, coords4):
    """Calculate the angle using the four atoms

    Args:
        coords1: First of four coordinates of form [x,y,z]
        coords2: Second of four
        coords3: Third of four
        coords4: Fourth of four
    Returns
        value: Size of the angle (float)
    """
    diff43 = np.array(coords4) - np.array(coords3)
    diff32 = np.array(coords3) - np.array(coords2)
    diff12 = np.array(coords1) - np.array(coords2)

    c12_32 = np.cross(diff12, diff32)
    c12_32 = normalize(c12_32)
    c43_32 = np.cross(diff43, diff32)
    c43_32 = normalize(c43_32)

    scal = np.inner(c12_32, c43_32)
    if np.absolute(scal + 1.0) < SMALL:
        value = 180.0
    elif np.absolute(scal - 1.0) < SMALL:
        value = 0.0
    else:
        value = DIHEDRAL * math.acos(scal)

    chiral = np.inner(np.cross(c12_32, c43_32), diff32)
    if chiral < 0:
        value = value * -1.0
    return value
