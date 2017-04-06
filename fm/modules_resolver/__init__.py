# optparse.py
# CLI options parser.
#
# Copyright (C) 2016  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

import solv


class ModulesResolverSolution(object):
    """
    Class representing solution for a ModulesResolverProblem.
    """
    def __init__(self, solution):
        """
        Creates new ModulesResolverSolution instance.
        """
        #: User-level description of the solution.
        self.desc = ""
        elements = solution.elements(True)
        for element in elements:
            self.desc += "- %s\n" % element.str()

        #: Solution to be passed to ModulesResolver.solve_install
        #: or ModulesResolver.solve_erase methods on next
        #: call to finish the original call of these methods.
        self.solution = []
        for element in solution.elements():
            if element.str().find("do not ask to") == -1:
                self.solution.append(element.Job())


class ModulesResolverProblem(object):
    """
    Class representing problem during the dependency solving.
    """
    def __init__(self, id2mmd, problem):
        """
        Creates new ModulesResolverProblem instance.
        """
        #: User-leve description of the problem
        self.desc = str(problem)
        self.mmd = None
        self.other_mmd = None
        self.dep = None

        if problem.findproblemrule().info().solvable:
            self.mmd = id2mmd[problem.findproblemrule().info().solvable]
        if problem.findproblemrule().info().othersolvable:
            self.other_mmd = id2mmd[problem.findproblemrule().info().othersolvable]
        if problem.findproblemrule().info().dep:
            self.dep = problem.findproblemrule().info().dep

        #: List of acceptable solution. One of these solutions
        #: should be passed to ModulesResolver.solve_install
        #: or ModulesResolver.solve_erase methods on next
        #: call to finish the original call of these methods.
        self.solutions = []
        solutions = problem.solutions()
        for solution in solutions:
            solution = ModulesResolverSolution(solution)
            if len(solution.solution) != 0:
                self.solutions.append(solution)


class ModulesResolverResult(object):
    """
    Class representing the result of module solving done by for example
    ModulesResolver.solve_install.
    """

    def __init__(self, id2mmd, problems, trans = None):
        """
        Creates new ModulesResolver instance.
        """

        #: List of modules to erase to fulfill the dependencies.
        self.to_disable = []
        #: List of modules to install to fulfill the dependencies.
        self.to_enable = []
        #: List of modules to reinstall to fulfill the dependencies.
        self.to_reinstall = []
        #: List of modules to downgrade to fulfill the dependencies.
        self.to_downgrade = []
        #: List of modules to upgrade to fulfill the dependencies.
        self.to_upgrade = []
        #: List of problems (ModulesResolverProblem) found during solving.
        self.problems = []

        for problem in problems:
            self.problems.append(ModulesResolverProblem(id2mmd, problem))

        if not trans or trans.isempty():
            return

        for cl in trans.classify(solv.Transaction.SOLVER_TRANSACTION_SHOW_OBSOLETES | solv.Transaction.SOLVER_TRANSACTION_OBSOLETE_IS_UPGRADE):
            for p in cl.solvables():
                if cl.type == solv.Transaction.SOLVER_TRANSACTION_ERASE:
                    self.to_disable.append(id2mmd[p])
                elif cl.type == solv.Transaction.SOLVER_TRANSACTION_INSTALL:
                    self.to_enable.append(id2mmd[p])
                elif cl.type == solv.Transaction.SOLVER_TRANSACTION_REINSTALLED:
                    self.to_reinstall.append(id2mmd[p])
                elif cl.type == solv.Transaction.SOLVER_TRANSACTION_DOWNGRADED:
                    op = trans.othersolvable(p)
                    self.to_downgrade.append((id2mmd[p], id2mmd[op]))
                elif cl.type == solv.Transaction.SOLVER_TRANSACTION_UPGRADED:
                    op = trans.othersolvable(p)
                    self.to_upgrade.append((id2mmd[p], id2mmd[op]))


class ModulesResolver(object):
    """
    Class for module-level dependency solving.
    """

    def __init__(self):
        """
        Created new ModulesResolver instance.
        """
        #: libsolv Pool
        self.pool = solv.Pool()
        self.pool.setarch("x86_64")

        #: libsolv repo for enabled (installed) modules.
        self.enabled = self.pool.add_repo("enabled")
        self.pool.installed = self.enabled

        #: libsolv repo for all available modules.
        self.available = self.pool.add_repo("available")

        self._id2mmd = {}
        self._requires_operator = solv.REL_EQ | solv.REL_GT

    def set_default_requires_operator(self, strategy):
        """
        Sets default operator for requirements computing.
        Possible `strategy` values:
        - "==" - Requirements are treated as the particular version only.
        - ">=" - Requirements are treated as particular version or greater.
        """
        if strategy == "==":
            self._requires_operator = solv.REL_EQ
        elif strategy == ">=":
            self._requires_operator = solv.REL_EQ | solv.REL_GT

    def _create_solvable(self, repo, mmd):
        """
        Creates libsolv Solvable object from the module metadata and
        associate it with the particular repo.

        :param Repo repo: Libsolv repository.
        :param ModuleMetadata mmd: Module metadata to create Solvable from.
        """
        solvable = repo.add_solvable()
        solvable.name = mmd.name
        solvable.evr = str(mmd.version)
        solvable.arch = "x86_64"
        solvable.mmd = mmd

        # Provides
        solvable.add_provides(self.pool.Dep(mmd.name).Rel(solv.REL_EQ, self.pool.Dep(solvable.evr)))
        solvable.add_provides(self.pool.Dep(mmd.name).Rel(solv.REL_EQ, self.pool.Dep(None)))

        # Requires
        for req_name, version in mmd.requires.items():
            # Workaround for broken modulemd parsing...
            if version == "None":
                version = None
            solvable.add_requires(self.pool.Dep(req_name).Rel(self._requires_operator, self.pool.Dep(version)))

        self._id2mmd[solvable] = mmd

        return solvable

    def add_enabled_mmd(self, mmd):
        """
        Adds Module Metadata of enabled (installed) module.

        :param ModuleMetadata mmd: Module metadata.
        """
        self._create_solvable(self.enabled, mmd)

    def add_available_mmd(self, mmd):
        """
        Adds Module Metadata of available module.

        :param ModuleMetadata mmd: Module metadata.
        """
        self._create_solvable(self.available, mmd)

    def _solve(self, arg, job_type, solutions = []):
        """
        Executes libsolv job, also applying the passed solution list.

        :param string arg: Argument to pass to libsolv (usually module name)
        """

        # Generate the whatprovides list.
        self.pool.createwhatprovides()

        # Create the solver.
        solver = self.pool.Solver()

        # Try to select the module we are interested in.
        flags = solv.Selection.SELECTION_NAME|solv.Selection.SELECTION_PROVIDES|solv.Selection.SELECTION_GLOB
        flags |= solv.Selection.SELECTION_CANON|solv.Selection.SELECTION_DOTARCH|solv.Selection.SELECTION_REL
        sel = self.pool.select(arg, flags)
        if sel.isempty():
            return None

        # Prepare the job including the solution for problems from previous calls.
        jobs = sel.jobs(job_type)
        jobs += solutions

        # Try to solve the dependencies.
        problems = solver.solve(jobs)

        # In case we have some problems, return early here with the problems.
        if len(problems) != 0:
            return ModulesResolverResult(self._id2mmd, problems)

        # In case there are no problems, parse the results and return.
        trans = solver.transaction()
        del solver
        return ModulesResolverResult(self._id2mmd, problems, trans)

    def solve_enable(self, mod_name, solutions = []):
        """
        Returns the steps which need to be done to enable particular module.

        :param string mod_name: Name of the module to enable.
        :param list solutions: Solutions which should solve the problems identified
        in the previous call of this method. See ModulesResolverProblem for more info.
        """
        return self._solve(mod_name, solv.Job.SOLVER_INSTALL, solutions)

    def solve_disable(self, mod_name, solutions = []):
        """
        Returns the steps which need to be done to disable particular module.

        :param string mod_name: Name of the module to disable.
        :param list solutions: Solutions which should solve the problems identified
        in the previous call of this method. See ModulesResolverProblem for more info.
        """
        return self._solve(mod_name, solv.Job.SOLVER_ERASE, solutions)

    def solve_update(self, mod_name, solutions = []):
        """
        Returns the steps which need to be done to update particular module.

        :param string mod_name: Name of the module to update.
        :param list solutions: Solutions which should solve the problems identified
        in the previous call of this method. See ModulesResolverProblem for more info.
        """
        return self._solve(mod_name, solv.Job.SOLVER_UPDATE, solutions)