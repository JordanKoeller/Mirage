#include "simulationview.h"
#include <QApplication>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    SimulationView w;
    w.show();

    return a.exec();
}
