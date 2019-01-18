#include "simulationview.h"
#include "ui_simulationview.h"

SimulationView::SimulationView(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::SimulationView)
{
    ui->setupUi(this);
}

SimulationView::~SimulationView()
{
    delete ui;
}
