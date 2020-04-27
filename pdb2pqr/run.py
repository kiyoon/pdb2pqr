"""Routines for running the code with a given set of options and PDB files."""
import logging
import time
import io
from . import utilities
from . import definitions
from . import protein
from . import routines
from . import hydrogens
from . import forcefield
from . import aa
from . import na
from . import pdb
from . import __version__


_LOGGER = logging.getLogger(__name__)


def getOldHeader(pdblist):
    """Get old header from list of PDBs.

    Args:
        pdblist:  list of PDBs
    
    Returns:
        Old header as string.
    """
    oldHeader = io.StringIO()
    headerTypes = (pdb.HEADER, pdb.TITLE, pdb.COMPND, pdb.SOURCE, pdb.KEYWDS,
                   pdb.EXPDTA, pdb.AUTHOR, pdb.REVDAT, pdb.JRNL, pdb.REMARK,
                   pdb.SPRSDE, pdb.NUMMDL)
    for pdbObj in pdblist:
        if not isinstance(pdbObj,headerTypes):
            break

        oldHeader.write(str(pdbObj))
        oldHeader.write('\n')

    return oldHeader.getvalue()


def printPQRHeaderCIF(pdblist,
                      atomlist,
                      reslist,
                      charge,
                      ff,
                      ph_calc_method,
                      pH,
                      ffout,
                      include_old_header=False):

    """
        Print the header for the PQR file in cif format.

        Paramaters:
            atomlist: A list of atoms that were unable to have
                      charges assigned (list)
            reslist:  A list of residues with non-integral charges
                      (list)
            charge:   The total charge on the protein (float)
            ff:       The forcefield name (string)
            pH :  pH value, if any. (float)
            ffout :  ff used for naming scheme (string)
        Returns
            header:   The header for the PQR file (string)
    """

    if(ff is None):
        ff = "User force field"
    else:
        ff = ff.upper()

    header = "#\n"
    header += "loop_\n"
    header += "_pdbx_database_remark.id\n"
    header += "_pdbx_database_remark.text\n"
    header += "1\n"
    header += ";\n"
    header += "PQR file generated by PDB2PQR (Version %s)\n" % __version__
    header += "\n"
    header += "Forcefiled used: %s\n" % ff
    if(not ffout is None):
        header += "Naming scheme used: %s\n" % ffout
    header += "\n"
    if(ph_calc_method is not None):
        header += "pKas calculated by %s and assigned using pH %.2f\n" % (ph_calc_method, pH)
    header += ";\n"
    header +="2\n"
    header +=";\n"
    if len(atomlist) > 0:
        header += "Warning: PDB2PQR was unable to assign charges\n"
        header += "to the following atoms (omitted below):\n"
        for atom in atomlist:
            header += "             %i %s in %s %i\n" % \
                      (atom.get("serial"), atom.get("name"), \
                       atom.get("residue").get("name"), \
                       atom.get("residue").get("resSeq"))
        header += "This is usually due to the fat thtat this residue is not\n"
        header += "an amino acid or nucleic acid; or, there are no parameters\n"
        header += "available for the specific protonation state of this\n"
        header += "residue in the selected forcefield.\n"
    if len(reslist) > 0:
        header += "\n"
        header += "Warning: Non-integral net charges were found in\n"
        header += "the following residues:\n"
        for residue in reslist:
            header += "              %s - Residue Charge: %.4f\n" % \
                      (residue, residue.getCharge())
    header += ";\n"
    header += "3\n"
    header += ";\n"
    header += "Total charge on this protein: %.4f e\n" % charge
    header += ";\n"
    if include_old_header:
        header += "4\n"
        header += ";\n"
        header += "Including original cif header is not implemented yet.\n"
        header += ";\n"
    header += "#\n"
    header += "loop_\n"
    header += "_atom_site.group_PDB\n"
    header += "_atom_site.id\n"
    header += "_atom_site.label_atom_id\n"
    header += "_atom_site.label_comp_id\n"
    header += "_atom_site.label_seq_id\n"
    header += "_atom_site.Cartn_x\n"
    header += "_atom_site.Cartn_y\n"
    header += "_atom_site.Cartn_z\n"
    header += "_atom_site.pqr_partial_charge\n"
    header += "_atom_site.pqr_radius\n"

    return header


def printPQRHeader(pdblist,
                   atomlist,
                   reslist,
                   charge,
                   ff,
                   ph_calc_method,
                   pH,
                   ffout,
                   include_old_header=False):
    """
        Print the header for the PQR file

        Parameters:
            atomlist: A list of atoms that were unable to have
                      charges assigned (list)
            reslist:  A list of residues with non-integral charges
                      (list)
            charge:   The total charge on the protein (float)
            ff:       The forcefield name (string)
            pH :  pH value, if any. (float)
            ffout :  ff used for naming scheme (string)
        Returns
            header:   The header for the PQR file (string)
    """
    if ff is None:
        ff = 'User force field'
    else:
        ff = ff.upper()
    header = "REMARK   1 PQR file generated by PDB2PQR (Version %s)\n" % __version__
    header = header + "REMARK   1\n"
    header = header + "REMARK   1 Forcefield Used: %s\n" % ff
    if not ffout is None:
        header = header + "REMARK   1 Naming Scheme Used: %s\n" % ffout
    header = header + "REMARK   1\n"

    if ph_calc_method is not None:
        header = header + "REMARK   1 pKas calculated by %s and assigned using pH %.2f\n" % (ph_calc_method, pH)
        header = header + "REMARK   1\n"

    if len(atomlist) != 0:
        header += "REMARK   5 WARNING: PDB2PQR was unable to assign charges\n"
        header += "REMARK   5          to the following atoms (omitted below):\n"
        for atom in atomlist:
            header += "REMARK   5              %i %s in %s %i\n" % \
                      (atom.get("serial"), atom.get("name"), \
                       atom.get("residue").get("name"), \
                       atom.get("residue").get("resSeq"))
        header += "REMARK   5 This is usually due to the fact that this residue is not\n"
        header += "REMARK   5 an amino acid or nucleic acid; or, there are no parameters\n"
        header += "REMARK   5 available for the specific protonation state of this\n"
        header += "REMARK   5 residue in the selected forcefield.\n"
        header += "REMARK   5\n"
    if len(reslist) != 0:
        header += "REMARK   5 WARNING: Non-integral net charges were found in\n"
        header += "REMARK   5          the following residues:\n"
        for residue in reslist:
            header += "REMARK   5              %s - Residue Charge: %.4f\n" % \
                      (residue, residue.getCharge())
        header += "REMARK   5\n"
    header += "REMARK   6 Total charge on this protein: %.4f e\n" % charge
    header += "REMARK   6\n"

    if include_old_header:
        header += "REMARK   7 Original PDB header follows\n"
        header += "REMARK   7\n"

        header += getOldHeader(pdblist)

    return header


def runPDB2PQR(pdblist, options):
    """
        Run the PDB2PQR Suite

        Args:
            pdblist: The list of objects that was read from the PDB file
                     given as input (list)
            options: The name of the forcefield (string)

        Returns
            A dictionary with the following elements:
            * header:  The PQR file header (string)
            * lines:  The PQR file atoms (list)
            * missed_ligands:  A list of ligand residue names whose charges could not be assigned (ligand)
            * protein:  The protein object
    """

    pkaname = ""
    lines = []
    Lig = None
    atomcount = 0   # Count the number of ATOM records in pdb

    outroot = utilities.getPQRBaseFileName(options.output_pqr)

    if options.pka_method == 'propka':
        pkaname = outroot + ".propka"
        #TODO: What? Shouldn't it be up to propka on how to handle this?
        if os.path.isfile(pkaname):
            os.remove(pkaname)

    start = time.time()
    _LOGGER.info("Beginning PDB2PQR...")

    myDefinition = definitions.Definition()
    _LOGGER.info("Parsed Amino Acid definition file.")

    if options.drop_water:
        # Remove the waters
        pdblist_new = []
        for record in pdblist:
            if isinstance(record, (pdb.HETATM, pdb.ATOM, pdb.SIGATM,
                                   pdb.SEQADV)):
                if record.resName in aa.WAT.water_residue_names:
                    continue
            pdblist_new.append(record)

        pdblist = pdblist_new

    # Check for the presence of a ligand!  This code is taken from pdb2pka/pka.py

    if options.ligand is not None:
        myProtein, myDefinition, Lig = ligff.initialize(myDefinition,
                                                        options.ligand,
                                                        pdblist)
        for atom in myProtein.getAtoms():
            if atom.type == "ATOM":
                atomcount += 1
    else:
        myProtein = protein.Protein(pdblist, myDefinition)

    _LOGGER.info("Created protein object:")
    _LOGGER.info("  Number of residues in protein: %s", myProtein.numResidues())
    _LOGGER.info("  Number of atoms in protein   : %s", myProtein.numAtoms())

    myRoutines = routines.Routines(myProtein)

    for residue in myProtein.getResidues():
        multoccupancy = 0
        for atom in residue.getAtoms():
            if atom.altLoc != "":
                multoccupancy = 1
                txt = "Warning: multiple occupancies found: %s in %s." % (atom.name, residue)
                _LOGGER.warn(txt)
        if multoccupancy == 1:
            _LOGGER.warn("WARNING: multiple occupancies found in %s at least one of the instances is being ignored.", residue)

    myRoutines.setTermini(options.neutraln, options.neutralc)
    myRoutines.updateBonds()

    if options.clean:
        header = ""
        lines = myProtein.printAtoms(myProtein.getAtoms(), options.chain)

        # Process the extensions
        for ext in options.active_extensions:
            module = extensions.extDict[ext]
            module.run_extension(myRoutines, outroot, extensionOptions)

        _LOGGER.debug("Total time taken: %.2f seconds", (time.time() - start))

        #Be sure to include None for missed ligand residues
        results_dict = {"header": header, "lines": lines,
                        "missed_ligands": None, "protein": myProtein}
        return results_dict

    #remove any future need to convert to lower case
    if options.ff is not None:
        ff = options.ff.lower()
    if options.ffout is not None:
        ffout = options.ffout.lower()

    if not options.assign_only:
        # It is OK to process ligands with no ATOM records in the pdb
        if atomcount == 0 and Lig != None:
            pass
        else:
            myRoutines.findMissingHeavy()
        myRoutines.updateSSbridges()

        if options.debump:
            myRoutines.debumpProtein()

        if options.pka_method == 'propka':
            myRoutines.runPROPKA(ph, ff, outroot, pkaname, ph_calc_options, version=31)
        elif options.pka_method == 'pdb2pka':
            myRoutines.runPDB2PKA(ph, ff, pdblist, ligand, ph_calc_options)

        myRoutines.addHydrogens()

        myhydRoutines = hydrogens.hydrogenRoutines(myRoutines)

        if options.debump:
            myRoutines.debumpProtein()

        if options.opt:
            myhydRoutines.setOptimizeableHydrogens()
            # TONI fixing residues - myhydRoutines has a reference to myProtein, so i'm altering it in place
            myRoutines.holdResidues(None)
            myhydRoutines.initializeFullOptimization()
            myhydRoutines.optimizeHydrogens()
        else:
            myhydRoutines.initializeWaterOptimization()
            myhydRoutines.optimizeHydrogens()

        # Special for GLH/ASH, since both conformations were added
        myhydRoutines.cleanup()


    else:  # Special case for HIS if using assign-only
        for residue in myProtein.getResidues():
            if isinstance(residue, aa.HIS):
                myRoutines.applyPatch("HIP", residue)

    myRoutines.setStates()

    myForcefield = forcefield.Forcefield(ff, myDefinition, options.userff,
                                         options.usernames)
    hitlist, misslist = myRoutines.applyForcefield(myForcefield)

    ligsuccess = 0

    if options.ligand is not None:
        # If this is independent, we can assign charges and radii here
        for residue in myProtein.getResidues():
            if isinstance(residue, LIG):
                templist = []
                Lig.make_up2date(residue)
                for atom in residue.getAtoms():
                    atom.ffcharge = Lig.ligand_props[atom.name]["charge"]
                    atom.radius = Lig.ligand_props[atom.name]["radius"]
                    if atom in misslist:
                        misslist.pop(misslist.index(atom))
                        templist.append(atom)

                charge = residue.getCharge()
                if abs(charge - int(charge)) > 0.001:
                    # Ligand parameterization failed
                    _LOGGER.warn("WARNING: PDB2PQR could not successfully parameterize the desired ligand; it has been left out of the PQR file.")

                    # remove the ligand
                    myProtein.residues.remove(residue)
                    for myChain in myProtein.chains:
                        if residue in myChain.residues: myChain.residues.remove(residue)
                else:
                    ligsuccess = 1
                    # Mark these atoms as hits
                    hitlist = hitlist + templist

    # Temporary fix; if ligand was successful, pull all ligands from misslist
    if ligsuccess:
        templist = misslist[:]
        for atom in templist:
            if isinstance(atom.residue, (aa.Amino, na.Nucleic)):
                continue
            misslist.remove(atom)

    # Create the Typemap
    if options.typemap:
        typemapname = "%s-typemap.html" % outroot
        myProtein.createHTMLTypeMap(myDefinition, typemapname)

    # Grab the protein charge
    reslist, charge = myProtein.getCharge()

    # If we want a different naming scheme, use that

    if options.ffout is not None:
        scheme = ffout
        userff = None # Currently not supported
        if scheme != ff:
            myNameScheme = Forcefield(scheme, myDefinition, userff)
        else:
            myNameScheme = myForcefield
        myRoutines.applyNameScheme(myNameScheme)

    if(options.isCIF):
        header = printPQRHeaderCIF(pdblist, misslist, reslist, charge, ff,
                            options.pka_method, options.ph, options.ffout,
                            include_old_header=options.include_header)
    else:
        header = printPQRHeader(pdblist, misslist, reslist, charge, ff,
                            options.pka_method, options.ph, options.ffout,
                            include_old_header=options.include_header)

    lines = myProtein.printAtoms(hitlist, options.chain)

    # Determine if any of the atoms in misslist were ligands
    missedligandresidues = []
    for atom in misslist:
        if isinstance(atom.residue, (aa.Amino, na.Nucleic)):
            continue
        if atom.resName not in missedligandresidues:
            missedligandresidues.append(atom.resName)

    # Process the extensions
    for ext in options.active_extensions:
        module = extensions.extDict[ext]
        module.run_extension(myRoutines, outroot, extensionOptions)

    _LOGGER.debug("Total time taken: %.2f seconds", (time.time() - start))

    result_dict = {}
    result_dict["header"] = header
    result_dict["lines"] = lines
    result_dict["missed_ligands"] = missedligandresidues
    result_dict["protein"] = myProtein
    
    return result_dict
