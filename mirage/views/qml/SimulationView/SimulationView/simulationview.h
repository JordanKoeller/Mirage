#ifndef SIMULATIONVIEW_H
#define SIMULATIONVIEW_H

#include <QWidget>

namespace Ui {
class SimulationView;
}

class SimulationView : public QWidget
{
    Q_OBJECT

public:
    explicit SimulationView(QWidget *parent = nullptr);
    ~SimulationView();

private:
    Ui::SimulationView *ui;
};

#endif // SIMULATIONVIEW_H
