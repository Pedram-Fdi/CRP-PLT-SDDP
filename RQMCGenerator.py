import numpy as np
from Constants import Constants
from scipy.stats import qmc
from numpy.random import SeedSequence, default_rng

class RQMCGenerator(object):

    SavedValue = {}

    @staticmethod
    def AddToSavedValue(nrpoints, dimensionpoint, a):
        if Constants.Debug: print("\n We are in 'RQMCGenerator' Class -- AddToSavedValue")
        RQMCGenerator.SavedValue["%s_%s" % (nrpoints, dimensionpoint)] = a

    @staticmethod
    def GetFromSavedValue(nrpoints, dimensionpoint):
        if Constants.Debug: print("\n We are in 'RQMCGenerator' Class -- GetFromSavedValue")
        
        key = "%s_%s" % (nrpoints, dimensionpoint)
        if key in RQMCGenerator.SavedValue:
            return RQMCGenerator.SavedValue[key]
        else:
            return None

    @staticmethod
    def halton_sequence(size, dim):
        if Constants.Debug: print("\n We are in 'RQMCGenerator' Class -- halton_sequence")
        """Generate a Halton sequence of a given size and dimension."""
        def prime(n):
            """Return the nth prime number."""
            primes = [2]
            candidate = 3
            while len(primes) < n:
                if all(candidate % p != 0 for p in primes):
                    primes.append(candidate)
                candidate += 2
            return primes

        def van_der_corput(n, base):
            """Generate the Van der Corput sequence."""
            vdc, denom = 0, 1
            while n:
                n, remainder = divmod(n, base)
                denom *= base
                vdc += remainder / denom
            return vdc

        primes = prime(dim)
        sequence = np.zeros((size, dim))

        for j in range(dim):
            for i in range(size):
                sequence[i, j] = van_der_corput(i + 1, primes[j])

        return sequence

    @staticmethod
    def generate_sequence(nrpoints, dimensionpoint, sequence_type="Halton", scramble=False):
        """Generate low-discrepancy sequence points."""
        seed_seq = SeedSequence(Constants.SeedArray[0] + 1)  # Ensure reproducibility
        rng = default_rng(seed_seq)

        if sequence_type == "Halton":
            generator = qmc.Halton(d=dimensionpoint, scramble=scramble, seed=rng)
        elif sequence_type == "Sobol":
            generator = qmc.Sobol(d=dimensionpoint, scramble=scramble, seed=rng)
        elif sequence_type == "LHS":
            generator = qmc.LatinHypercube(d=dimensionpoint, seed=rng)
        else:
            raise ValueError("Unsupported sequence type")

        # Adjust nrpoints + 1 to skip the first all-zero point if QMC and not scrambled
        adjusted_nrpoints = nrpoints + 1 if (sequence_type == "Sobol" or "Halton") and not scramble else nrpoints
        points = generator.random(n=adjusted_nrpoints)

        # Skip the first row for QMC to avoid all-zero scenario
        if (sequence_type == "Sobol" or "Halton") and not scramble:
            points = points[1:]

        return points
    
    @staticmethod
    def RQMC01(nrpoints, dimensionpoint, withweight = True, QMC = False, sequence_type = Constants.SequenceTypee):
        if Constants.Debug:
            print("We are in 'RQMCGenerator' Class -- RQMC01")
            print("nrpoints, dimensionpoint, withweight, QMC: ", nrpoints, dimensionpoint, withweight, QMC)
            print("sequence_type: ", sequence_type)
        
        randomizer = [0] * dimensionpoint

        if QMC:
            # Generate one more point than needed
            nrpoints_adjusted = nrpoints + 1
        else:
            nrpoints_adjusted = nrpoints
        
        np.random.seed(Constants.SeedArray[0])

        if (not QMC):
            randomizer = [np.random.uniform(0.0, 10000000.0) for i in range(dimensionpoint)]

        if sequence_type == 'Halton':
            a = RQMCGenerator.GetFromSavedValue(nrpoints_adjusted, dimensionpoint)
            if a is None:
                a = RQMCGenerator.halton_sequence(nrpoints_adjusted, dimensionpoint)
                RQMCGenerator.AddToSavedValue(nrpoints_adjusted, dimensionpoint, a)
        elif sequence_type == 'LHS':
            sampler = qmc.LatinHypercube(d=dimensionpoint)
            a = sampler.random(n=nrpoints_adjusted)

        # Generate the sequence first
        result = []
        for i in range(nrpoints_adjusted):
            row = []
            for d in range(dimensionpoint):
                if sequence_type == 'Halton':
                    value = (((i * a[i, d] % nrpoints_adjusted) / float(nrpoints_adjusted)) + randomizer[d]) % 1.0
                elif sequence_type == 'LHS':
                    value = a[i, d]
                row.append(value)
            result.append(row)

        if QMC and sequence_type == 'Halton':
            result = result[1:]

        # with open('result.txt', 'w') as file:
        #     for row in result:
        #         file.write(f"{row}\n")
        # print("result:\n", result)
        return result
