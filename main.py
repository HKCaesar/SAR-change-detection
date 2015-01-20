import scipy.stats
import matplotlib.pyplot as plt
import matplotlib.colors
from sar_data import *
from plotting import *

# Ranges defining the forest region of the image
no_change_i = range(307, 455)
no_change_j = range(52, 120)

def aregion(X):
    return X[np.ix_(no_change_i, no_change_j)]

class Gamma(object):
    """
    Test statistic on equality of two Gamma parameters
    Use for change detection between two single channel SAR images X and Y
    n, m are Equivalent Number of Looks (ENL)
    """

    def __init__(self, X, Y, n, m):
        self.X = X
        self.Y = Y
        self.n = n
        self.m = m
        self.Q = Y/X # Test statistic

    def histogram(self, percentile):
        f, ax = plt.subplots(1, 1)
        ax.hist(self.Q.flatten(), bins=100, normed=True, range=(0,5))

        # Fisher's F overlay
        F = scipy.stats.f(2*self.m, 2*self.n)
        x = np.linspace(0, 5, 500)
        ax.plot(x, F.pdf(x))

        # Select threshold from distrib quantile
        t_inf, t_sup = F.ppf(percentile/2), F.ppf(1 - percentile/2)

        ax.axvline(t_inf, 0, 1, color='black', linestyle='--')
        # ax.text(t_inf, 1.12, " 5% percentile")
        ax.axvline(t_sup, 0, 1, color='black', linestyle='--')
        # ax.text(t_sup, 1.12, " 95% percentile")

        return f, ax
    
    def image_binary(self, percentile):
        F = scipy.stats.f(2*self.m, 2*self.n)
        t_inf, t_sup = F.ppf(percentile/2), F.ppf(1 - percentile/2)

        im = np.zeros_like(self.Q)
        im[self.Q < t_inf] = 1
        im[self.Q > t_sup] = 1

        return im

    def image_linear(self, percentile):
        pass

def wishart_test(X, Y, p, n, m):
    "Returns ln(Q) of the wishart test statistic"

    detX = determinant(X)
    detY = determinant(Y)
    detXY = determinant(sar_sum(X, Y))

    lnq = (p*(n+m)*np.log(n+m) - p*n*np.log(n) - p*m*np.log(m)
            + n*np.log(detX) + m*np.log(detY) - (n+m)*np.log(detXY))

    rho = 1 - (2*p*p - 1)/(6*p) * (1/n + 1/m - 1/(n+m))

    w2 = -(p*p/4)*(1-1/rho)**2 + p*p*(p*p - 1)/24 * (1/(n*n) + 1/(m*m) - 1/((n+m)**2))*1/(p*p)
    return lnq, rho, w2

def wishart_change_detection(april, may, n, m):
    "Wishart change detection"

    # Test statistic
    p = 3
    lnq, rho, w2 = wishart_test(april, may, p, n, m)

    # Extract no change region and test statistic
    april_no = region(april, no_change_i, no_change_j)
    may_no = region(may, no_change_i, no_change_j)
    lnq_no, rho, w2 = wishart_test(april_no, may_no, p, n, m)

    # Histogram of the no change region
    f, ax = plt.subplots(1, 1)
    ax.hist(-2*rho*lnq_no.flatten(), bins=100, normed=True)

    # Overlay pdf
    x = np.linspace(0, 50, 1000)
    chi2 = scipy.stats.chi2
    y = chi2.pdf(x, p**2) + w2*(chi2.pdf(x, p**2+4) - chi2.pdf(x, p**2))
    ax.plot(x, y)

    im = np.zeros_like(lnq)
    im[-2*rho*lnq > 30] = 1

    return f, ax, im

if __name__ == "__main__":

    # Load data
    april = SARData().load_april()
    may = SARData().load_may()

    # No change region
    april_no_change = region(april, no_change_i, no_change_j)
    may_no_change = region(may, no_change_i, no_change_j)

    # Color composites
    plt.imsave("fig/april.png", color_composite(april))
    plt.imsave("fig/may.png", color_composite(may))

    # Gamma test

    # No change region
    def gamma_test(april, may, channel, ENL, percent):
        # Data
        X = april.__dict__[channel]
        Y = may.__dict__[channel]
        Xno = aregion(X)
        Yno = aregion(Y)

        # Name variables
        short_channel = channel[:2].upper()
        hist_title = ("Likelihood ratio distribution of no change region {} ENL={}"
            .format(short_channel, ENL))
        hist_filename = "fig/gamma.hist.ENL{0}.{1}.{2:.2f}.png".format(ENL, short_channel, percent)
        im_filename = "fig/gamma.im.ENL{0}.{1}.{2:.2f}.png".format(ENL, short_channel, percent)

        # No change region histogram
        gno = Gamma(Xno, Yno, ENL, ENL)
        f, ax = gno.histogram(percent)
        ax.set_title(hist_title)
        f.savefig(hist_filename)

        # Binary image
        g = Gamma(X, Y, ENL, ENL)
        im = g.image_binary(percent)
        plt.imsave(im_filename, im, cmap='gray')

    gamma_test(april, may, "hhhh", 13, 0.01)
    gamma_test(april, may, "hvhv", 13, 0.01)
    gamma_test(april, may, "vvvv", 13, 0.01)

    gamma_test(april, may, "hhhh", 12, 0.01)
    gamma_test(april, may, "hvhv", 12, 0.01)
    gamma_test(april, may, "vvvv", 12, 0.01)

    # Wishart test
    # f, ax, im = wishart_change_detection(april, may, 13, 13)
    # ax.set_title(r"$-2 \rho \ln Q$ distribution in no change region")
    # f.savefig("fig/lnq.hist.png")
    # plt.imsave("fig/lnq.png", im, cmap='gray')
    # plt.close('all')
